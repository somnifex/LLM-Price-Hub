from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import StandardModel, User
from app.auth import get_current_admin

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("")
async def get_models(session: Session = Depends(get_session)):
    models = session.exec(select(StandardModel)).all()
    return models

@router.post("")
async def create_model(
    model: StandardModel,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model

@router.put("/{model_id}")
async def update_model(
    model_id: int,
    model_data: StandardModel,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    existing = session.get(StandardModel, model_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")
        
    existing.name = model_data.name
    existing.vendor = model_data.vendor
    session.add(existing)
    session.commit()
    return existing
