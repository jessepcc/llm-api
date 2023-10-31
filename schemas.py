"""Schemas for the chat app."""
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ChatResponse(BaseModel):
    """Chat response schema."""

    sender: str
    message: str
    type: str

    @validator("sender")
    def sender_must_be_bot_or_you(cls, v):
        if v not in ["bot", "you"]:
            raise ValueError("sender must be bot or you")
        return v

    @validator("type")
    def validate_message_type(cls, v):
        if v not in ["start", "stream", "end", "error", "info"]:
            raise ValueError("type must be start, stream or end")
        return v


""" Base, Read, Create and Update schemas for each model """


class UserBase(BaseModel):
    id: str
    email: str

    class Config:
        orm_mode = True


class Session(BaseModel):
    id: str
    sessionToken: str
    userId: int

    class Config:
        orm_mode = True


class Resume(BaseModel):
    id: str
    userId: int
    resource: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True


class Job(BaseModel):
    id: str
    title: str
    content: str
    company: str = None
    resource: str = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True


class Interview(BaseModel):
    id: str
    result: str
    history: str
    type: str
    user: UserBase
    userId: str
    jobId: str
    resumeId: str

    class Config:
        orm_mode = True


class InterviewTicket(BaseModel):
    id: str
    userId: str
    interviewId: str
    host: str
    createdAt: datetime
    expiredAt: datetime

    class Config:
        orm_mode = True
