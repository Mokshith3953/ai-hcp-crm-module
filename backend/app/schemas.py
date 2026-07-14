import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class InteractionCreate(BaseModel):
    hcp_name: str
    topic: str
    notes: str
    channel: str = "structured"
    hcp_specialty: str | None = None
    sentiment: str | None = None
    status: str = "Logged"
    follow_up_date: str | None = None
    interaction_type: str = "Meeting"
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: list[str] = []
    materials_shared: list[str] = []
    samples_distributed: list[str] = []
    outcomes: str | None = None
    follow_up_actions: str | None = None


class InteractionUpdate(BaseModel):
    hcp_name: str | None = None
    topic: str | None = None
    notes: str | None = None
    channel: str | None = None
    hcp_specialty: str | None = None
    sentiment: str | None = None
    status: str | None = None
    follow_up_date: str | None = None
    interaction_type: str | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: list[str] | None = None
    materials_shared: list[str] | None = None
    samples_distributed: list[str] | None = None
    outcomes: str | None = None
    follow_up_actions: str | None = None


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
    interaction_type: str
    interaction_date: str | None
    interaction_time: str | None
    attendees: list[str]
    materials_shared: list[str]
    samples_distributed: list[str]
    outcomes: str | None
    follow_up_actions: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "attendees", "materials_shared", "samples_distributed", mode="before"
    )
    @classmethod
    def _parse_json_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return []
        return value

    @field_validator("interaction_type", mode="before")
    @classmethod
    def _default_interaction_type(cls, value):
        return value or "Meeting"


class AgentRequest(BaseModel):
    message: str
    thread_id: str | None = None


class AgentResponse(BaseModel):
    reply: str
    thread_id: str
    tools_used: list[str]
    tools: list[str]


class SuggestFollowUpsRequest(BaseModel):
    topic: str = ""
    notes: str = ""
    outcomes: str = ""


class SuggestFollowUpsResponse(BaseModel):
    suggestions: list[str]
