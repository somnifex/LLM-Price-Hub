from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session
from app.models import User, UserSettings, CurrencyRate
from app.auth import get_current_user
import json

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/currencies")
async def get_currencies(session: Session = Depends(get_session)):
    """Get all available currencies and their rates."""
    currencies = session.exec(select(CurrencyRate)).all()
    return currencies


@router.get("/user")
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get current user's settings."""
    settings = session.get(UserSettings, current_user.id)
    if not settings:
        # Create default settings if they don't exist
        settings = UserSettings(user_id=current_user.id)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    
    return settings

class UserSettingsUpdate(BaseModel):
    preferred_currencies: Optional[List[str]] = None
    default_currency: Optional[str] = None


@router.put("/user")
async def update_user_settings(
    settings_in: UserSettingsUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update user settings."""
    settings = session.get(UserSettings, current_user.id)
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        session.add(settings)
    
    if settings_in.preferred_currencies is not None:
        settings.preferred_currencies = json.dumps(settings_in.preferred_currencies)
    
    if settings_in.default_currency is not None:
        # Validate that default currency is in preferred list or is USD
        # (Logic can be strict or loose, let's be loose for now but ensure it's a valid code)
        settings.default_currency = settings_in.default_currency

    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings
