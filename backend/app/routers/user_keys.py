from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_session
from app.models import User, UserSettings, UserAPIKey, Provider, ProviderStatus
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/user", tags=["user"])


class E2EESetupRequest(BaseModel):
    salt: str
    verification: str


class UserSettingsResponse(BaseModel):
    e2ee_enabled: bool
    e2ee_salt: Optional[str] = None
    e2ee_verification: Optional[str] = None


class AddAPIKeyRequest(BaseModel):
    provider_id: int
    api_key: str
    is_encrypted: bool
    note: Optional[str] = None


class APIKeyResponse(BaseModel):
    id: int
    provider_id: int
    provider_name: str
    api_key: str  # Encrypted ciphertext or plaintext (frontend handles masking)
    is_encrypted: bool
    note: Optional[str]
    created_at: str
    # Provider base URLs for easy access
    openai_base_url: Optional[str] = None
    gemini_base_url: Optional[str] = None
    claude_base_url: Optional[str] = None


class CreateProviderRequest(BaseModel):
    name: str
    website: Optional[str] = None
    openai_base_url: Optional[str] = None
    gemini_base_url: Optional[str] = None
    claude_base_url: Optional[str] = None
    submit_for_review: bool = False  # If true, set status to pending
    proof_type: Optional[str] = None  # 'image', 'text', 'url'
    proof_content: Optional[str] = None


class UpdateProviderRequest(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    openai_base_url: Optional[str] = None
    gemini_base_url: Optional[str] = None
    claude_base_url: Optional[str] = None


class ProviderResponse(BaseModel):
    id: int
    name: str
    website: Optional[str]
    status: str
    openai_base_url: Optional[str] = None
    gemini_base_url: Optional[str] = None
    claude_base_url: Optional[str] = None


# ============ User Settings Endpoints ============


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get user's E2EE settings."""
    settings = session.get(UserSettings, current_user.id)
    if not settings:
        return UserSettingsResponse(e2ee_enabled=False)

    return UserSettingsResponse(
        e2ee_enabled=settings.e2ee_enabled,
        e2ee_salt=settings.e2ee_salt,
        e2ee_verification=settings.e2ee_verification,
    )


@router.post("/settings/e2ee")
async def setup_e2ee(
    request: E2EESetupRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Enable E2EE for the user."""
    settings = session.get(UserSettings, current_user.id)

    if settings:
        settings.e2ee_enabled = True
        settings.e2ee_salt = request.salt
        settings.e2ee_verification = request.verification
    else:
        settings = UserSettings(
            user_id=current_user.id,
            e2ee_enabled=True,
            e2ee_salt=request.salt,
            e2ee_verification=request.verification,
        )
        session.add(settings)

    session.commit()
    return {"message": "E2EE enabled successfully"}


@router.delete("/settings/e2ee")
async def disable_e2ee(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Disable E2EE for the user."""
    settings = session.get(UserSettings, current_user.id)
    if settings:
        settings.e2ee_enabled = False
        settings.e2ee_salt = None
        settings.e2ee_verification = None
        session.commit()

    return {"message": "E2EE disabled successfully"}


# ============ API Keys Endpoints ============


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """List all API keys for the current user."""
    statement = select(UserAPIKey).where(UserAPIKey.user_id == current_user.id)
    results = session.exec(statement).all()

    response = []
    for key in results:
        provider = session.get(Provider, key.provider_id)
        response.append(
            APIKeyResponse(
                id=key.id,
                provider_id=key.provider_id,
                provider_name=provider.name if provider else "Unknown",
                api_key=key.api_key,
                is_encrypted=key.is_encrypted,
                note=key.note,
                created_at=key.created_at.isoformat(),
                openai_base_url=provider.openai_base_url if provider else None,
                gemini_base_url=provider.gemini_base_url if provider else None,
                claude_base_url=provider.claude_base_url if provider else None,
            )
        )

    return response


@router.post("/keys")
async def add_api_key(
    request: AddAPIKeyRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Add a new API key. Multiple keys per provider are allowed."""
    # Verify provider exists and is accessible
    provider = session.get(Provider, request.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Check if provider is private and belongs to another user
    if (
        provider.status == ProviderStatus.private
        and provider.owner_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Cannot access private provider")

    # Allow multiple keys per provider (no duplicate check)
    new_key = UserAPIKey(
        user_id=current_user.id,
        provider_id=request.provider_id,
        api_key=request.api_key,
        is_encrypted=request.is_encrypted,
        note=request.note,
    )
    session.add(new_key)
    session.commit()
    session.refresh(new_key)

    return {"message": "API key added successfully", "id": new_key.id}


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Delete an API key."""
    key = session.get(UserAPIKey, key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API key not found")

    session.delete(key)
    session.commit()
    return {"message": "API key deleted successfully"}


# ============ Providers Endpoints ============


@router.get("/providers", response_model=List[ProviderResponse])
async def list_user_providers(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """List user's own providers (private, pending, approved, rejected)."""
    statement = select(Provider).where(Provider.owner_id == current_user.id)
    results = session.exec(statement).all()

    return [
        ProviderResponse(
            id=p.id,
            name=p.name,
            website=p.website,
            status=p.status.value,
            openai_base_url=p.openai_base_url,
            gemini_base_url=p.gemini_base_url,
            claude_base_url=p.claude_base_url,
        )
        for p in results
    ]


@router.post("/providers")
async def create_provider(
    request: CreateProviderRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Create a new provider. Optionally submit for public review."""
    # Determine status based on submit_for_review flag
    if request.submit_for_review:
        if not request.proof_type or not request.proof_content:
            raise HTTPException(
                status_code=400,
                detail="Proof type and content required for public submission",
            )
        status = ProviderStatus.pending
    else:
        status = ProviderStatus.private

    new_provider = Provider(
        name=request.name,
        website=request.website,
        owner_id=current_user.id,
        status=status,
        openai_base_url=request.openai_base_url,
        gemini_base_url=request.gemini_base_url,
        claude_base_url=request.claude_base_url,
        proof_type=request.proof_type,
        proof_content=request.proof_content,
        is_official=False,
    )
    session.add(new_provider)
    session.commit()
    session.refresh(new_provider)

    message = "Provider created successfully"
    if request.submit_for_review:
        message = "Provider submitted for public review"

    return {"message": message, "id": new_provider.id}


@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: int,
    request: UpdateProviderRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Update a provider owned by the user."""
    provider = session.get(Provider, provider_id)
    if not provider or provider.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")

    if request.name is not None:
        provider.name = request.name
    if request.website is not None:
        provider.website = request.website
    if request.openai_base_url is not None:
        provider.openai_base_url = request.openai_base_url
    if request.gemini_base_url is not None:
        provider.gemini_base_url = request.gemini_base_url
    if request.claude_base_url is not None:
        provider.claude_base_url = request.claude_base_url

    session.commit()
    return {"message": "Provider updated successfully"}


@router.post("/providers/{provider_id}/submit")
async def submit_provider_for_review(
    provider_id: int,
    proof_type: str,
    proof_content: str,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Submit a private provider for public review."""
    provider = session.get(Provider, provider_id)
    if not provider or provider.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.status != ProviderStatus.private:
        raise HTTPException(
            status_code=400, detail="Provider already submitted or approved"
        )

    provider.status = ProviderStatus.pending
    provider.proof_type = proof_type
    provider.proof_content = proof_content
    session.commit()

    return {"message": "Provider submitted for review"}


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Delete a provider owned by the user."""
    provider = session.get(Provider, provider_id)
    if not provider or provider.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Check if any API keys are using this provider
    existing_keys = session.exec(
        select(UserAPIKey).where(UserAPIKey.provider_id == provider_id)
    ).first()

    if existing_keys:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete provider with existing API keys. Delete the keys first.",
        )

    session.delete(provider)
    session.commit()
    return {"message": "Provider deleted successfully"}
