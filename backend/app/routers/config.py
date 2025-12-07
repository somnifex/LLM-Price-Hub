from fastapi import APIRouter, Depends
from sqlmodel import Session, select, or_
from app.database import get_session
from app.models import CurrencyRate, Provider, User, ProviderStatus, SystemSetting
from typing import Optional

router = APIRouter(prefix="/api/config", tags=["config"])

# Optional dependency for get_current_user
async def get_current_user_optional():
    """Returns None if not authenticated, used for optional auth."""
    try:
        from app.auth import get_current_user
        from fastapi import Depends as _Depends
        # This is a workaround - we'll just return None for now
        # In practice, we should check token manually
        return None
    except:
        return None

@router.get("/rates")
async def get_rates(session: Session = Depends(get_session)):
    rates = session.exec(select(CurrencyRate)).all()
    return rates

@router.get("/providers")
async def get_providers(
    session: Session = Depends(get_session)
):
    """Get all public (approved) providers."""
    statement = select(Provider).where(Provider.status == ProviderStatus.approved)
    providers = session.exec(statement).all()
    return providers


@router.get("/public-settings")
async def get_public_settings(session: Session = Depends(get_session)):
    allowed = {"site_name", "home_display_mode", "force_email_verification"}
    settings = session.exec(select(SystemSetting)).all()
    return {s.key: s.value for s in settings if s.key in allowed}

