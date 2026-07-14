import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Interaction
from app.schemas import InteractionCreate, InteractionUpdate

LIST_FIELDS = ("attendees", "materials_shared", "samples_distributed")


def _encode_lists(data: dict) -> dict:
    for field in LIST_FIELDS:
        if field in data and data[field] is not None:
            data[field] = json.dumps(data[field])
    return data


def list_interactions(db: Session, limit: int = 50) -> list[Interaction]:
    return (
        db.query(Interaction)
        .order_by(Interaction.created_at.desc())
        .limit(limit)
        .all()
    )


def get_interaction(db: Session, interaction_id: int) -> Interaction | None:
    return db.get(Interaction, interaction_id)


def create_interaction(db: Session, payload: InteractionCreate) -> Interaction:
    interaction = Interaction(**_encode_lists(payload.model_dump()))
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def update_interaction(
    db: Session, interaction_id: int, payload: InteractionUpdate
) -> Interaction | None:
    interaction = get_interaction(db, interaction_id)
    if interaction is None:
        return None
    data = _encode_lists(payload.model_dump(exclude_unset=True))
    for field, value in data.items():
        setattr(interaction, field, value)
    db.commit()
    db.refresh(interaction)
    return interaction


def search_interactions(db: Session, query: str, limit: int = 10) -> list[Interaction]:
    pattern = f"%{query}%"
    return (
        db.query(Interaction)
        .filter(
            or_(
                Interaction.hcp_name.ilike(pattern),
                Interaction.hcp_specialty.ilike(pattern),
                Interaction.topic.ilike(pattern),
                Interaction.notes.ilike(pattern),
            )
        )
        .order_by(Interaction.created_at.desc())
        .limit(limit)
        .all()
    )


def recent_interactions_for_hcp(
    db: Session, hcp_name: str | None, limit: int = 5
) -> list[Interaction]:
    q = db.query(Interaction)
    if hcp_name:
        q = q.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    return q.order_by(Interaction.created_at.desc()).limit(limit).all()
