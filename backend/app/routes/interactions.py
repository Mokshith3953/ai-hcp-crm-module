from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import InteractionCreate, InteractionOut, InteractionUpdate

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


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
