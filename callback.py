"""Callback handlers used in the app."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult

from schemas import ChatResponse
from speech import synthesize_text


class StreamingLLMCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming LLM responses."""

    def __init__(self, websocket_manager, websocket, type: str = "text"):
        self.websocket_manager = websocket_manager
        self.websocket = websocket
        self.type = type

    async def on_llm(self, *args, **kwargs) -> None:
        pass

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        pass
        # stream response to client
        # resp = ChatResponse(sender="bot", message=token, type="stream")
        # await self.websocket.send_json(resp.dict())
        """Run when new token."""

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM ends running."""
        pass

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        pass

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        pass
        """Run when chain ends running."""

        # TODO handle error
        # TODO handle duplicate with on_agent_finish
        # if "output" in outputs:
        #     if self.type == "text":
        #         resp = ChatResponse(
        #             sender="bot", message=outputs["output"], type="stream"
        #         )
        #         await self.websocket_manager.send_dict_message(
        #             resp.dict(), self.websocket
        #         )
        #     elif self.type == "voice":
        #         speech = synthesize_text(outputs["output"])
        #         await self.websocket.send_bytes(speech)

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        # TODO handle error
        # TODO handle duplicate with on_chain_end
        if "output" in finish.return_values:
            if self.type == "text":
                resp = ChatResponse(
                    sender="bot", message=finish.return_values["output"], type="stream"
                )
                await self.websocket_manager.send_dict_message(
                    resp.dict(), self.websocket
                )
            elif self.type == "voice":
                speech = synthesize_text(finish.return_values["output"])
                await self.websocket_manager.send_binary_message(speech, self.websocket)
