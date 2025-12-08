from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
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
    Review,
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


class UserRoleUpdate(BaseModel):
    role: str


class UserSuspensionRequest(BaseModel):
    reason: Optional[str] = None
    suspended_until: Optional[datetime] = None


class UserDeleteRequest(BaseModel):
    purge_reviews: bool = True


def _ensure_can_manage_user(target: User, actor: User):
    """Admins can manage basic users; super admins can manage anyone."""
    if actor.role == "super_admin":
        return

    if actor.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to manage users")

    if target.role != "user":
        raise HTTPException(
            status_code=403,
            detail="Admins can only manage standard users",
        )


def _recompute_provider_score(session: Session, provider_id: int):
    """Recalculate provider average rating after moderation actions."""
    rating_rows = session.exec(
        select(Review.rating).where(Review.provider_id == provider_id)
    ).all()
    ratings = [
        r[0] if isinstance(r, tuple) else r  # SQLAlchemy can return either shape
        for r in rating_rows
    ]
    provider = session.get(Provider, provider_id)
    if provider:
        provider.avg_score = sum(ratings) / len(ratings) if ratings else 0.0
        session.add(provider)


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
    query = select(User)
    if current_user.role == "admin":
        query = query.where(User.role == "user")

    users = session.exec(query).all()

    # Aggregate contributions for quick insight
    price_counts = {
        user_id: count
        for user_id, count in session.exec(
            select(ModelPrice.submitter_id, func.count(ModelPrice.id))
            .where(ModelPrice.submitter_id.is_not(None))
            .group_by(ModelPrice.submitter_id)
        )
    }
    review_counts = {
        user_id: count
        for user_id, count in session.exec(
            select(Review.user_id, func.count(Review.id))
            .where(Review.user_id.is_not(None))
            .group_by(Review.user_id)
        )
    }

    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "suspended_until": u.suspended_until.isoformat()
            if u.suspended_until
            else None,
            "suspension_reason": u.suspension_reason,
            "email_verified": u.email_verified,
            "created_at": u.created_at.isoformat(),
            "price_count": price_counts.get(u.id, 0),
            "review_count": review_counts.get(u.id, 0),
        }
        for u in users
    ]


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


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    payload: UserSuspensionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    _ensure_can_manage_user(user, current_user)

    user.is_active = False
    user.suspended_until = payload.suspended_until
    user.suspension_reason = payload.reason or "Suspended by administrator"
    session.add(user)
    session.commit()
    return {"message": "User suspended"}


@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    _ensure_can_manage_user(user, current_user)

    user.is_active = True
    user.suspended_until = None
    user.suspension_reason = None
    session.add(user)
    session.commit()
    return {"message": "User restored"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    payload: UserDeleteRequest = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    if payload is None:
        payload = UserDeleteRequest()

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "super_admin":
        # Prevent deleting last super admin
        remaining_supers = session.exec(
            select(User).where((User.role == "super_admin") & (User.id != user_id))
        ).all()
        if not remaining_supers:
            raise HTTPException(
                status_code=400, detail="At least one super admin is required"
            )

    _ensure_can_manage_user(user, current_user)

    affected_provider_ids = set()
    removed_reviews = 0
    if payload.purge_reviews:
        reviews = session.exec(select(Review).where(Review.user_id == user_id)).all()
        for review in reviews:
            if review.provider_id:
                affected_provider_ids.add(review.provider_id)
            session.delete(review)
            removed_reviews += 1

    session.delete(user)
    session.commit()

    for pid in affected_provider_ids:
        _recompute_provider_score(session, pid)
    session.commit()

    return {
        "message": "User deleted",
        "removed_reviews": removed_reviews,
    }


@router.get("/users/{user_id}/reviews")
async def list_user_reviews(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    _ensure_can_manage_user(user, current_user)

    statement = (
        select(Review, Provider)
        .join(Provider, Review.provider_id == Provider.id, isouter=True)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    results = session.exec(statement).all()

    return [
        {
            "id": review.id,
            "provider_id": review.provider_id,
            "provider_name": provider.name if provider else None,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat(),
        }
        for review, provider in results
    ]


@router.delete("/users/{user_id}/reviews/{review_id}")
async def delete_user_review(
    user_id: int,
    review_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    _ensure_can_manage_user(user, current_user)

    review = session.get(Review, review_id)
    if not review or review.user_id != user_id:
        raise HTTPException(status_code=404, detail="Review not found")

    provider_id = review.provider_id
    session.delete(review)
    session.commit()

    if provider_id:
        _recompute_provider_score(session, provider_id)
        session.commit()

    return {"message": "Review deleted"}


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
