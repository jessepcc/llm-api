"""Main entrypoint for the app."""
from datetime import datetime
import logging
import os
from typing import Annotated, List
from functools import lru_cache
from pathlib import Path
from typing import Union
from tempfile import NamedTemporaryFile
import asyncio
from dotenv import load_dotenv

from fastapi import (
    BackgroundTasks,
    Cookie,
    Depends,
    FastAPI,
    Query,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from langchain.schema import messages_to_dict

from pydantic import BaseSettings, BaseModel

from sqlalchemy.orm import Session

import crud

from schemas import ChatResponse, Job
from ingest import ingest_docs, ingest_text
from database import get_db_session, test_db_connection
from agent import chat_agent
from task import generate_report, generate_mock

from evaluate_agent import evaluate_agent
from callback import StreamingLLMCallbackHandler

from stt import Deepgram_STT
import openai

from redis import asyncio as aioredis


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        case_sensitive = True


app = FastAPI()
origins = ["http://localhost:3000", "https://chat-job-in.vercel.app"]
gd_client = Deepgram_STT()
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_dict_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def send_binary_message(self, message: bytes, websocket: WebSocket):
        await websocket.send_bytes(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


websocket_manager = ConnectionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache()
def get_settings():
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    return Settings()


async def test_redis_connection():
    redis_url = os.environ["REDIS_URL"]
    connection = aioredis.from_url(redis_url)
    try:
        await connection.ping()
        # await connection.ping()
    finally:
        await connection.close()


@app.on_event("startup")
async def startup_event():
    # setup openai
    openai.api_base = os.environ["OPENAI_API_BASE"]
    openai.api_type = os.environ["OPENAI_API_TYPE"]
    await test_db_connection()
    # test redis connection
    await test_redis_connection()


# create job duty
# create item
@app.get("/jd/", response_model=List[Job])
def create_jd(
    skip: int = 0, limit: int = 100, db_session: Session = Depends(get_db_session)
):
    db_jobs = crud.get_job_list(db_session, skip=skip, limit=limit)
    if db_jobs is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_jobs


# check valid session
def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[Union[str, None], Cookie()] = None,
    token: Annotated[Union[str, None], Query()] = None,
    db_session: Session = Depends(get_db_session),
):
    # TODO: check if session is valid
    # print("session", session)
    print("session", session)
    print("token", token)
    if session is None or token is None or "user" not in session:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    # TODO session invalid
    valid_session = crud.get_session_by_id(db_session, token, session)

    if valid_session is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return valid_session


# add endpoint for setup job role
@app.websocket("/interview/{interview_id}/ws")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
    interview_id: str,
    t: str,
    db_session: Session = Depends(get_db_session),
):  # CHECK VALIDITY
    result = crud.get_interview_by_id(db_session, interview_id)
    client_host = websocket.client.host

    if t is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    # test if have a valid ticket
    interviewTicket = crud.get_interview_ticket(db_session, t)
    # if interview ticket is not expired
    # TODO check host
    if (
        interviewTicket is None
        or interviewTicket.expiredAt < datetime.now()
        # or interviewTicket.host != client_host
    ):
        print(interviewTicket)
        print(datetime.now())
        print(">>>> fail load interview")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if (
        result is None
        or "job" not in result
        or "resume" not in result
        or "interview" not in result
        or result["interview"].result is not None
        or result["interview"].history is not None
    ):
        print(">>>> fail load interview")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    interview_type = result["interview"].type

    vs = await ingest_docs(
        index="r_" + result["resume"].id, input=result["resume"].resource
    )

    job_input = f'Job Title: {result["job"].title} Employer: {result["job"].company } Job Description: {result["job"].content}'

    job_vs = await ingest_text(index="j_" + result["job"].id, input=job_input)

    # create agent specific to this chat
    new_chat = chat_agent(
        vs,
        job_vs,
    )
    print(">>>> chat agent created")

    await websocket_manager.connect(websocket)
    start_resp = ChatResponse(sender="bot", message="", type="start")
    await websocket.send_json(start_resp.dict())

    timeout_count = 0

    while True:
        try:
            print(">>>> waiting for message")

            data = await asyncio.wait_for(websocket.receive(), timeout=30)
            websocket._raise_on_disconnect(data)

            timeout_count = 0

            question, transcribed = None, None

            if "text" in data:
                question = data["text"]
                print('">>>> received: ', question)
                if question == ">>>>INTERVIEW TIMESUP<<<<":
                    print(">>>> close here")
                    end_resp = ChatResponse(
                        sender="bot", message="<<<<INTERVIEW TIMESUP>>>>", type="end"
                    )
                    await websocket.send_json(end_resp.dict())
                    websocket_manager.disconnect(websocket)
                    break
            elif "bytes" in data:
                # in voice
                print(">>>> received bytes")
                # data = await websocket.receive_bytes()
                # create a array buffer
                temp = NamedTemporaryFile(suffix=".webm", delete=False)
                with temp as audio:
                    audio.write(data["bytes"])
                transcribed = await gd_client.transcribe_from_file(temp.name)

                os.remove(temp.name)

            input = transcribed if transcribed is not None else question
            if input is not None:
                result = await new_chat.arun(
                    input,
                    callbacks=[
                        StreamingLLMCallbackHandler(
                            websocket_manager, websocket, type=interview_type
                        )
                    ],
                )
                end_resp = ChatResponse(sender="bot", message="", type="end")
                await websocket.send_json(end_resp.dict())

        except asyncio.TimeoutError:
            timeout_count += 1
            # timeout more than 4 times, max 2.5min
            if timeout_count > 4:
                websocket_manager.disconnect(websocket)
                break
        except WebSocketDisconnect:
            logging.info("websocket disconnect")
            websocket_manager.disconnect(websocket)
            break
        except Exception as e:
            logging.error(e)
            resp = ChatResponse(
                sender="bot",
                message="Sorry, something went wrong.",
                type="error",
            )
            await websocket.send_json(resp.dict())

    # TODO save chat history
    print(new_chat.memory.buffer)
    dicts = messages_to_dict(new_chat.memory.buffer)
    print(">>>> save interview history")
    if dicts is not None and len(dicts) > 0:
        crud.add_interview_history(db_session, interview_id, dicts)


@app.post("/evaluate/{interview_id}")
async def evaluate_interview(
    interview_id: str,
    # cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db_session),
):
    result = crud.get_interview_by_id(db_session, interview_id)
    print(result)
    if (
        result is None
        or "job" not in result
        or "resume" not in result
        or "interview" not in result
        or result["interview"].result is not None
        or result["interview"].history is None
        or len(result["interview"].history) == 0
    ):
        print(">>>> fail load interview")
        raise HTTPException(status_code=404, detail="Invalid interview")
    background_tasks.add_task(generate_report, interview_id, result, db_session)
    background_tasks.add_task(generate_mock, interview_id, result, db_session)
    return crud.add_pending_interview_result(db_session, interview_id)


@app.post("/add-history/{interview_id}")
def add_history(
    interview_id: str,
    # cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
    db_session: Session = Depends(get_db_session),
):
    history = ["GG"]
    interview = crud.add_interview_history(db_session, interview_id, history)
    print(">>>>> finish", interview)
    # get the interview history
    # llm for evaluation
    # get the vectorstore of the jd and resume
    # in redis first, if no -> create
    # redis id => id the resume and the jd
    return interview
    # return {**interview, 'resume_resource': interview[1], 'job_content':interview[2]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
