from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredential
from sqlmodel import Session, select, or_
from app.database import get_session
from app.models import CurrencyRate, Provider, User, ProviderStatus
from typing import Optional

router = APIRouter(prefix="/api/config", tags=["config"])

security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthCredential] = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """Returns None if not authenticated, used for optional auth."""
    if not credentials:
        return None
    
    try:
        from jose import jwt, JWTError
        from app.auth import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        return user
    except (JWTError, Exception):
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

