from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Interaction
from app.schemas import InteractionCreate, InteractionUpdate


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
    interaction = Interaction(**payload.model_dump())
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
    for field, value in payload.model_dump(exclude_unset=True).items():
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
