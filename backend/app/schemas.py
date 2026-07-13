from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InteractionCreate(BaseModel):
    hcp_name: str
    topic: str
    notes: str
    channel: str = "structured"
    hcp_specialty: str | None = None
    sentiment: str | None = None
    status: str = "Logged"
    follow_up_date: str | None = None


class InteractionUpdate(BaseModel):
    hcp_name: str | None = None
    topic: str | None = None
    notes: str | None = None
    channel: str | None = None
    hcp_specialty: str | None = None
    sentiment: str | None = None
    status: str | None = None
    follow_up_date: str | None = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hcp_name: str
    hcp_specialty: str | None
    topic: str
    notes: str
    channel: str
    sentiment: str | None
    status: str
    follow_up_date: str | None
    created_at: datetime
    updated_at: datetime


class AgentRequest(BaseModel):
    message: str
    thread_id: str | None = None


class AgentResponse(BaseModel):
    reply: str
    thread_id: str
    tools_used: list[str]
    tools: list[str]
