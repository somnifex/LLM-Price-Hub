from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from app.database import get_session
from app.models import (
    ModelPrice,
    PriceStatus,
    User,
    SystemSetting,
    Provider,
    ProviderStatus,
    StandardModel,
    StandardModelRequest,
)
from app.auth import get_current_admin, get_current_super_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ApproveModelRequestData(BaseModel):
    name: Optional[str] = None  # Override requested name if needed
    vendor: Optional[str] = None


class StandardModelIn(BaseModel):
    name: str
    vendor: Optional[str] = None
    official_currency: Optional[str] = "USD"
    official_input_price: Optional[float] = None
    official_output_price: Optional[float] = None
    is_featured: Optional[bool] = False
    rank_hint: Optional[int] = None


@router.get("/pending")
async def get_pending_prices(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """Get pending price submissions with provider and model info."""
    statement = (
        select(ModelPrice, Provider, StandardModel)
        .join(Provider, ModelPrice.provider_id == Provider.id)
        .join(StandardModel, ModelPrice.standard_model_id == StandardModel.id)
        .where(ModelPrice.status == PriceStatus.pending)
    )

    results = session.exec(statement).all()
    return [
        {
            "id": price.id,
            "provider_name": provider.name,
            "model_name": model.name,
            "provider_model_name": price.provider_model_name,
            "input_price": price.input_price,
            "output_price": price.output_price,
            "currency": price.currency,
            "proof_type": price.proof_type,
            "proof_content": price.proof_content,
            "proof_img_path": price.proof_img_path,
            "created_at": price.created_at.isoformat(),
        }
        for price, provider, model in results
    ]


@router.post("/approve/{price_id}")
async def approve_price(
    price_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    price = session.get(ModelPrice, price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")

    price.status = PriceStatus.active
    price.verified_at = datetime.utcnow()
    session.commit()
    return {"message": "Price approved"}


@router.post("/reject/{price_id}")
async def reject_price(
    price_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    price = session.get(ModelPrice, price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")

    price.status = PriceStatus.rejected
    session.commit()
    return {"message": "Price rejected"}


# ============ Standard Models Management ============


@router.get("/models")
async def admin_list_models(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    models = session.exec(select(StandardModel)).all()
    return models


@router.post("/models")
async def admin_create_model(
    model_in: StandardModelIn,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    model = StandardModel(**model_in.dict())
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.put("/models/{model_id}")
async def admin_update_model(
    model_id: int,
    model_in: StandardModelIn,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    model = session.get(StandardModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    for k, v in model_in.dict().items():
        setattr(model, k, v)

    session.add(model)
    session.commit()
    session.refresh(model)
    return model


@router.delete("/models/{model_id}")
async def admin_delete_model(
    model_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    model = session.get(StandardModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    session.delete(model)
    session.commit()
    return {"message": "Model deleted"}


# ============ Standard Model Requests ============


@router.get("/model-requests/pending")
async def list_model_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    requests = session.exec(
        select(StandardModelRequest).where(StandardModelRequest.status == "pending")
    ).all()
    return requests


@router.post("/model-requests/{request_id}/approve")
async def approve_model_request(
    request_id: int,
    payload: ApproveModelRequestData,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    req = session.get(StandardModelRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "approved"

    name = payload.name or req.requested_name
    vendor = payload.vendor or req.vendor

    existing = session.exec(select(StandardModel).where(StandardModel.name == name)).first()
    if existing:
        model = existing
        if vendor:
            model.vendor = vendor
    else:
        model = StandardModel(name=name, vendor=vendor)
        session.add(model)

    session.add(req)
    session.commit()
    session.refresh(model)
    return {"message": "Request approved", "model_id": model.id}


@router.post("/model-requests/{request_id}/reject")
async def reject_model_request(
    request_id: int,
    notes: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    req = session.get(StandardModelRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "rejected"
    req.admin_notes = notes
    session.add(req)
    session.commit()
    return {"message": "Request rejected"}


# ============ Provider Review ============


@router.get("/providers/pending")
async def get_pending_providers(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """Get pending provider submissions."""
    statement = (
        select(Provider, User)
        .join(User, Provider.owner_id == User.id)
        .where(Provider.status == ProviderStatus.pending)
    )

    results = session.exec(statement).all()
    return [
        {
            "id": provider.id,
            "name": provider.name,
            "website": provider.website,
            "openai_base_url": provider.openai_base_url,
            "gemini_base_url": provider.gemini_base_url,
            "claude_base_url": provider.claude_base_url,
            "proof_type": provider.proof_type,
            "proof_content": provider.proof_content,
            "submitter_email": user.email,
            "created_at": provider.created_at.isoformat(),
        }
        for provider, user in results
    ]


@router.post("/providers/{provider_id}/approve")
async def approve_provider(
    provider_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    provider = session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.status != ProviderStatus.pending:
        raise HTTPException(status_code=400, detail="Provider is not pending")

    provider.status = ProviderStatus.approved
    session.commit()
    return {"message": "Provider approved"}


@router.post("/providers/{provider_id}/reject")
async def reject_provider(
    provider_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    provider = session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.status != ProviderStatus.pending:
        raise HTTPException(status_code=400, detail="Provider is not pending")

    provider.status = ProviderStatus.rejected
    session.commit()
    return {"message": "Provider rejected"}


# ============ Model Request Review ============


@router.get("/models/pending")
async def get_pending_model_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """Get pending standard model requests."""
    statement = (
        select(StandardModelRequest, User)
        .join(User, StandardModelRequest.requester_id == User.id)
        .where(StandardModelRequest.status == "pending")
    )

    results = session.exec(statement).all()
    return [
        {
            "id": request.id,
            "requested_name": request.requested_name,
            "vendor": request.vendor,
            "requester_email": user.email,
            "created_at": request.created_at.isoformat(),
        }
        for request, user in results
    ]


@router.post("/models/{request_id}/approve")
async def approve_model_request(
    request_id: int,
    data: ApproveModelRequestData = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """Approve model request and create standard model."""
    request = session.get(StandardModelRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")

    # Create standard model with optional name/vendor override
    model_name = data.name if data and data.name else request.requested_name
    model_vendor = data.vendor if data and data.vendor else request.vendor

    new_model = StandardModel(name=model_name, vendor=model_vendor)
    session.add(new_model)

    request.status = "approved"
    session.commit()
    session.refresh(new_model)

    return {"message": "Model request approved", "model_id": new_model.id}


@router.post("/models/{request_id}/reject")
async def reject_model_request(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    request = session.get(StandardModelRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")

    request.status = "rejected"
    session.commit()
    return {"message": "Model request rejected"}


# ============ User Management ============


@router.get("/users")
async def get_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    users = session.exec(select(User)).all()
    for u in users:
        u.password_hash = "***"
    return users


class UserRoleUpdate(BaseModel):
    role: str


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_super_admin),
):
    role = role_update.role
    if role not in ["admin", "user", "super_admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    session.commit()
    return {"message": "User role updated"}


# ============ System Settings ============


@router.get("/settings")
async def get_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    settings = session.exec(select(SystemSetting)).all()
    return {s.key: s.value for s in settings}


@router.put("/settings")
async def update_settings(
    settings: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_super_admin),
):
    needs_reschedule = False
    needs_rate_refresh = False
    for key, value in settings.items():
        if key == "exchange_rate_interval_minutes":
            needs_reschedule = True
        if key in {"exchange_rate_url", "exchange_rate_key", "exchange_rate_provider"}:
            needs_rate_refresh = True

        if key == "home_display_mode":
            allowed_modes = {"table", "cards", "chart"}
            if str(value) not in allowed_modes:
                raise HTTPException(status_code=400, detail="Invalid home_display_mode")

        setting = session.get(SystemSetting, key)
        if not setting:
            setting = SystemSetting(key=key, value=str(value))
        else:
            setting.value = str(value)
        session.add(setting)
    session.commit()

    if needs_reschedule:
        from app.services.scheduler import reschedule_exchange_job

        reschedule_exchange_job()

    if needs_rate_refresh:
        try:
            from app.services.scheduler import update_exchange_rates

            update_exchange_rates()
        except Exception:
            # Keep request successful even if refresh fails; logs already captured inside updater
            pass

    return {"message": "Settings updated"}
