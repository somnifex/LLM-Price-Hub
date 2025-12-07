import shutil
import os
from app.auth import get_current_user
from app.models import (
    ModelPrice,
    Provider,
    CurrencyRate,
    StandardModel,
    PriceStatus,
    User,
    ProviderStatus,
    StandardModelRequest,
)
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlmodel import Session, select, desc, or_
from app.database import get_session
from datetime import datetime
from pydantic import BaseModel, Field as PydanticField

# Helpers
def _rate_map(session: Session) -> dict[str, float]:
    rates = session.exec(select(CurrencyRate)).all()
    rate_map = {r.code: r.rate_to_usd for r in rates}
    rate_map["USD"] = 1.0
    return rate_map


def _convert(amount: Optional[float], src: str, target: str, rate_map: dict[str, float]) -> Optional[float]:
    if amount is None:
        return None
    if src not in rate_map or target not in rate_map:
        return None
    usd = amount / rate_map[src]
    return usd * rate_map[target]

router = APIRouter(prefix="/api/prices", tags=["prices"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class PriceEntryIn(BaseModel):
    standard_model_id: Optional[int] = None
    new_model_name: Optional[str] = None
    new_model_vendor: Optional[str] = None
    provider_model_name: Optional[str] = None

    price_in: float
    price_out: float
    cache_hit_input_price: Optional[float] = None
    cache_hit_output_price: Optional[float] = None
    currency: str = "USD"

    proof_type: Optional[str] = None  # 'text' | 'url'
    proof_content: Optional[str] = None


class BatchSubmitRequest(BaseModel):
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    provider_website: Optional[str] = None
    openai_base_url: Optional[str] = None
    gemini_base_url: Optional[str] = None
    claude_base_url: Optional[str] = None
    submit_provider_for_review: bool = False
    provider_proof_type: Optional[str] = None
    provider_proof_content: Optional[str] = None

    prices: List[PriceEntryIn]


@router.post("/submit")
async def submit_price(
    # Provider info
    provider_id: Optional[int] = Form(None),
    provider_name: Optional[str] = Form(None),
    provider_website: Optional[str] = Form(None),
    openai_base_url: Optional[str] = Form(None),
    gemini_base_url: Optional[str] = Form(None),
    claude_base_url: Optional[str] = Form(None),
    submit_provider_for_review: bool = Form(False),
    provider_proof_type: Optional[str] = Form(None),
    provider_proof_content: Optional[str] = Form(None),
    # Model info
    standard_model_id: Optional[int] = Form(None),
    new_model_name: Optional[str] = Form(None),
    new_model_vendor: Optional[str] = Form(None),
    provider_model_name: Optional[str] = Form(None),  # Provider's custom model name
    # Price info
    price_in: float = Form(...),
    price_out: float = Form(...),
    currency: str = Form("USD"),
    # Proof (flexible)
    proof_type: Optional[str] = Form(None),  # 'image', 'text', 'url'
    proof_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Unified price submission with:
    - Select existing provider or create new
    - Select existing standard model or request new
    - Flexible proof types (image, text, URL)
    """

    # 1. Handle Provider
    if provider_id:
        provider = session.get(Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        # Check access if private
        if (
            provider.status == ProviderStatus.private
            and provider.owner_id != current_user.id
        ):
            raise HTTPException(
                status_code=403, detail="Cannot access private provider"
            )
    elif provider_name:
        # Create new provider
        provider_status = (
            ProviderStatus.pending
            if submit_provider_for_review
            else ProviderStatus.private
        )

        # Check for existing approved provider with same name
        existing = session.exec(
            select(Provider).where(
                Provider.name == provider_name,
                Provider.status == ProviderStatus.approved,
            )
        ).first()
        if existing:
            provider = existing
        else:
            provider = Provider(
                name=provider_name,
                website=provider_website,
                owner_id=current_user.id,
                status=provider_status,
                openai_base_url=openai_base_url,
                gemini_base_url=gemini_base_url,
                claude_base_url=claude_base_url,
                proof_type=provider_proof_type,
                proof_content=provider_proof_content,
                is_official=False,
            )
            session.add(provider)
            session.commit()
            session.refresh(provider)
    else:
        raise HTTPException(status_code=400, detail="Provider ID or name required")

    # 2. Handle Model
    model_request_id = None
    if standard_model_id:
        model = session.get(StandardModel, standard_model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Standard model not found")
    elif new_model_name:
        # Check if model exists
        existing_model = session.exec(
            select(StandardModel).where(StandardModel.name == new_model_name)
        ).first()
        if existing_model:
            model = existing_model
        else:
            # Create model request
            model_request = StandardModelRequest(
                requested_name=new_model_name,
                vendor=new_model_vendor,
                requester_id=current_user.id,
            )
            session.add(model_request)
            session.commit()
            session.refresh(model_request)
            model_request_id = model_request.id

            # Use a placeholder - admin will need to approve model first
            # For now, we'll create a pending placeholder
            raise HTTPException(
                status_code=202,
                detail=f"Model request submitted. ID: {model_request_id}. Please wait for admin approval before submitting price.",
            )
    else:
        raise HTTPException(
            status_code=400, detail="Standard model ID or new model name required"
        )

    # 3. Handle Proof
    proof_img_path = None
    if proof_type == "image" and file:
        file_ext = file.filename.split(".")[-1] if file.filename else "png"
        filename = f"{datetime.now().timestamp()}_{provider.name}.{file_ext}".replace(
            " ", "_"
        )
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        proof_img_path = f"static/uploads/{filename}"
        proof_content = proof_img_path  # Store path in content too

    # 4. Create Price Record
    price_record = ModelPrice(
        provider_id=provider.id,
        standard_model_id=model.id,
        submitter_id=current_user.id,
        provider_model_name=provider_model_name,
        input_price=price_in,
        output_price=price_out,
        currency=currency,
        proof_type=proof_type,
        proof_content=proof_content,
        proof_img_path=proof_img_path,
        status=PriceStatus.pending,
    )

    session.add(price_record)
    session.commit()
    session.refresh(price_record)

    return {
        "message": "Price submitted successfully",
        "id": price_record.id,
        "provider_id": provider.id,
        "provider_status": provider.status.value,
    }


@router.post("/submit-batch")
async def submit_price_batch(
    payload: BatchSubmitRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Batch submit prices for a single provider across multiple models."""

    # Handle provider
    if payload.provider_id:
        provider = session.get(Provider, payload.provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        if (
            provider.status == ProviderStatus.private
            and provider.owner_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Cannot access private provider")
    elif payload.provider_name:
        provider_status = (
            ProviderStatus.pending
            if payload.submit_provider_for_review
            else ProviderStatus.private
        )
        provider = Provider(
            name=payload.provider_name,
            website=payload.provider_website,
            owner_id=current_user.id,
            status=provider_status,
            openai_base_url=payload.openai_base_url,
            gemini_base_url=payload.gemini_base_url,
            claude_base_url=payload.claude_base_url,
            proof_type=payload.provider_proof_type,
            proof_content=payload.provider_proof_content,
            is_official=False,
        )
        session.add(provider)
        session.commit()
        session.refresh(provider)
    else:
        raise HTTPException(status_code=400, detail="Provider ID or name required")

    created_prices: list[int] = []

    for entry in payload.prices:
        # Resolve model
        model = None
        if entry.standard_model_id:
            model = session.get(StandardModel, entry.standard_model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Standard model not found")
        elif entry.new_model_name:
            existing_model = session.exec(
                select(StandardModel).where(StandardModel.name == entry.new_model_name)
            ).first()
            if existing_model:
                model = existing_model
            else:
                model = StandardModel(
                    name=entry.new_model_name,
                    vendor=entry.new_model_vendor,
                )
                session.add(model)
                session.commit()
                session.refresh(model)
        else:
            raise HTTPException(
                status_code=400, detail="Standard model ID or new model name required"
            )

        price_record = ModelPrice(
            provider_id=provider.id,
            standard_model_id=model.id,
            submitter_id=current_user.id,
            provider_model_name=entry.provider_model_name,
            input_price=entry.price_in,
            output_price=entry.price_out,
            cache_hit_input_price=entry.cache_hit_input_price,
            cache_hit_output_price=entry.cache_hit_output_price,
            currency=entry.currency,
            proof_type=entry.proof_type,
            proof_content=entry.proof_content,
            status=PriceStatus.pending,
        )
        session.add(price_record)
        session.commit()
        session.refresh(price_record)
        created_prices.append(price_record.id)

    return {
        "message": "Batch submitted",
        "provider_id": provider.id,
        "created_price_ids": created_prices,
        "provider_status": provider.status.value,
    }


@router.get("/compare/{standard_model_id}")
async def compare_prices(
    standard_model_id: int,
    target_currency: str = Query("USD"),
    session: Session = Depends(get_session),
):
    """Compare prices across providers for a model."""
    rate_map = _rate_map(session)

    if target_currency not in rate_map:
        raise HTTPException(status_code=400, detail="Target currency not supported")

    # Only show approved providers
    query = (
        select(ModelPrice, Provider)
        .join(Provider)
        .where(
            ModelPrice.standard_model_id == standard_model_id,
            ModelPrice.status == PriceStatus.active,
            or_(
                Provider.status == ProviderStatus.approved, Provider.is_official == True
            ),
        )
    )
    results = session.exec(query).all()

    response = []
    for price, provider in results:
        final_in = _convert(price.input_price, price.currency, target_currency, rate_map)
        final_out = _convert(price.output_price, price.currency, target_currency, rate_map)
        final_cache_in = _convert(price.cache_hit_input_price, price.currency, target_currency, rate_map)
        final_cache_out = _convert(price.cache_hit_output_price, price.currency, target_currency, rate_map)

        response.append(
            {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "provider_model_name": price.provider_model_name,
                "provider_score": provider.avg_score,
                "uptime": provider.uptime_rate,
                "original_currency": price.currency,
                "price_in": final_in,
                "price_out": final_out,
                "cache_hit_input_price": final_cache_in,
                "cache_hit_output_price": final_cache_out,
                "verified_at": (
                    price.verified_at.isoformat() if price.verified_at else None
                ),
                "proof_type": price.proof_type,
                "proof_content": price.proof_content,
                "proof": price.proof_img_path,
            }
        )

    response.sort(key=lambda x: x["price_in"])
    return response


@router.get("/highlights")
async def price_highlights(
    limit: int = Query(8, ge=1, le=50),
    target_currency: str = Query("USD"),
    session: Session = Depends(get_session),
):
    """Return top N featured/default models with official, platform avg, and lowest provider info."""

    rate_map = _rate_map(session)
    if target_currency not in rate_map:
        raise HTTPException(status_code=400, detail="Target currency not supported")

    # Pick models: featured first then fallback by popularity / rank_hint
    model_stmt = (
        select(StandardModel)
        .order_by(
            desc(StandardModel.is_featured),
            StandardModel.rank_hint,
            desc(StandardModel.popularity_score),
            StandardModel.id,
        )
        .limit(limit)
    )
    models = session.exec(model_stmt).all()

    payload = []
    for model in models:
        # Official price from model fields
        official_in = _convert(model.official_input_price, model.official_currency, target_currency, rate_map)
        official_out = _convert(model.official_output_price, model.official_currency, target_currency, rate_map)

        # Prices from providers
        price_stmt = (
            select(ModelPrice, Provider)
            .join(Provider)
            .where(
                ModelPrice.standard_model_id == model.id,
                ModelPrice.status == PriceStatus.active,
                or_(
                    Provider.status == ProviderStatus.approved,
                    Provider.is_official == True,
                ),
            )
        )
        price_rows = session.exec(price_stmt).all()

        platform_prices: list[dict] = []
        lowest = None
        for price, provider in price_rows:
            pin = _convert(price.input_price, price.currency, target_currency, rate_map)
            pout = _convert(price.output_price, price.currency, target_currency, rate_map)
            if pin is None or pout is None:
                continue
            platform_prices.append({"in": pin, "out": pout})
            if lowest is None or pin < lowest["price_in"]:
                lowest = {
                    "provider_id": provider.id,
                    "provider_name": provider.name,
                    "price_in": pin,
                    "price_out": pout,
                    "currency": target_currency,
                }

        avg_in = sum(p["in"] for p in platform_prices) / len(platform_prices) if platform_prices else None
        avg_out = sum(p["out"] for p in platform_prices) / len(platform_prices) if platform_prices else None

        payload.append(
            {
                "id": model.id,
                "name": model.name,
                "vendor": model.vendor,
                "official_price_in": official_in,
                "official_price_out": official_out,
                "official_currency": model.official_currency,
                "platform_avg_in": avg_in,
                "platform_avg_out": avg_out,
                "lowest": lowest,
            }
        )

    return payload


@router.get("/models")
async def list_models(session: Session = Depends(get_session)):
    """List all standard models."""
    models = session.exec(select(StandardModel)).all()
    return models


@router.post("/models/request")
async def request_new_model(
    name: str = Form(...),
    vendor: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Request a new standard model to be added."""
    # Check if already exists
    existing = session.exec(
        select(StandardModel).where(StandardModel.name == name)
    ).first()
    if existing:
        return {"message": "Model already exists", "model_id": existing.id}

    # Check if already requested
    pending = session.exec(
        select(StandardModelRequest).where(
            StandardModelRequest.requested_name == name,
            StandardModelRequest.status == "pending",
        )
    ).first()
    if pending:
        return {"message": "Model already requested", "request_id": pending.id}

    request = StandardModelRequest(
        requested_name=name, vendor=vendor, requester_id=current_user.id
    )
    session.add(request)
    session.commit()
    session.refresh(request)

    return {"message": "Model request submitted", "request_id": request.id}


@router.put("/{price_id}")
async def update_price(
    price_id: int,
    price_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    price = session.get(ModelPrice, price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")

    if (
        current_user.role not in ["admin", "super_admin"]
        and price.submitter_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    if "input_price" in price_data:
        price.input_price = price_data["input_price"]
    if "output_price" in price_data:
        price.output_price = price_data["output_price"]
    if "currency" in price_data:
        price.currency = price_data["currency"]

    session.commit()
    return {"message": "Price updated"}
