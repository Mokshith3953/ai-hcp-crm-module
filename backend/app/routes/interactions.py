import json

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.llm import get_llm
from app.schemas import (
    InteractionCreate,
    InteractionOut,
    InteractionUpdate,
    SuggestFollowUpsRequest,
    SuggestFollowUpsResponse,
)

router = APIRouter(prefix="/api/interactions", tags=["interactions"])

SUGGEST_PROMPT = """You are a pharma field-rep assistant. Based on this HCP
interaction, suggest 2-4 short, concrete next-step follow-up actions a rep could
take (e.g. scheduling a meeting, sending a specific document, adding a contact to
a list). Respond with ONLY a JSON array of short strings, no prose.

Topic: {topic}
Notes: {notes}
Outcomes: {outcomes}"""


@router.get("", response_model=list[InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return crud.list_interactions(db)


@router.post("", response_model=InteractionOut, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    return crud.create_interaction(db, payload)


@router.patch("/{interaction_id}", response_model=InteractionOut)
def update_interaction(
    interaction_id: int, payload: InteractionUpdate, db: Session = Depends(get_db)
):
    updated = crud.update_interaction(db, interaction_id, payload)
    if updated is None:
        raise HTTPException(404, "Interaction not found")
    return updated


@router.post("/suggest-followups", response_model=SuggestFollowUpsResponse)
def suggest_followups(payload: SuggestFollowUpsRequest):
    if not (payload.topic or payload.notes or payload.outcomes):
        return SuggestFollowUpsResponse(suggestions=[])

    llm = get_llm()
    response = llm.invoke(
        [
            HumanMessage(
                content=SUGGEST_PROMPT.format(
                    topic=payload.topic, notes=payload.notes, outcomes=payload.outcomes
                )
            )
        ]
    )
    content = response.content.strip().strip("`")
    if content.startswith("json\n"):
        content = content[5:]
    try:
        suggestions = json.loads(content)
        if not isinstance(suggestions, list):
            suggestions = []
    except (json.JSONDecodeError, ValueError):
        suggestions = []

    return SuggestFollowUpsResponse(suggestions=[str(s) for s in suggestions][:4])
