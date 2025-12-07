import shutil
import os
from app.auth import get_current_user
from app.models import (
    ModelPrice, Provider, CurrencyRate, StandardModel, PriceStatus, 
    User, ProviderStatus, StandardModelRequest
)
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlmodel import Session, select, desc, or_
from app.database import get_session
from datetime import datetime

router = APIRouter(prefix="/api/prices", tags=["prices"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/submit")
async def submit_price(
    # Provider info
    provider_id: Optional[int] = Form(None),  # Use existing provider
    provider_name: Optional[str] = Form(None),  # Or create new
    provider_website: Optional[str] = Form(None),
    openai_base_url: Optional[str] = Form(None),
    gemini_base_url: Optional[str] = Form(None),
    claude_base_url: Optional[str] = Form(None),
    submit_provider_for_review: bool = Form(False),
    provider_proof_type: Optional[str] = Form(None),
    provider_proof_content: Optional[str] = Form(None),
    
    # Model info
    standard_model_id: Optional[int] = Form(None),  # Use existing standard model
    new_model_name: Optional[str] = Form(None),  # Or request new
    new_model_vendor: Optional[str] = Form(None),
    provider_model_name: Optional[str] = Form(None),  # Provider's custom model name
    
    # Price info
    price_in: float = Form(...),
    price_out: float = Form(...),
    currency: str = Form("USD"),
    
    # Proof (flexible)
    proof_type: Optional[str] = Form(None),  # 'image', 'text', 'url'
    proof_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),  # Optional image upload
    
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Unified price submission with:
    - Select existing provider or create new
    - Select existing standard model or request new
    - Flexible proof types (image, text, URL)
    """
    
    # Validate prices
    if price_in < 0 or price_out < 0:
        raise HTTPException(status_code=400, detail="Prices cannot be negative")
    if price_in > 1000000 or price_out > 1000000:
        raise HTTPException(status_code=400, detail="Price seems unusually high. Please verify.")
    
    # 1. Handle Provider
    if provider_id:
        # Use existing provider
        provider = session.get(Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        # Check access if private
        if provider.status == ProviderStatus.private and provider.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot access private provider")
    elif provider_name:
        # Create new provider
        provider_status = ProviderStatus.pending if submit_provider_for_review else ProviderStatus.private
        
        # Check for existing approved provider with same name
        existing = session.exec(
            select(Provider).where(
                Provider.name == provider_name,
                Provider.status == ProviderStatus.approved
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
                is_official=False
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
                requester_id=current_user.id
            )
            session.add(model_request)
            session.commit()
            session.refresh(model_request)
            model_request_id = model_request.id
            
            # Use a placeholder - admin will need to approve model first
            # For now, we'll create a pending placeholder
            raise HTTPException(
                status_code=202,
                detail=f"Model request submitted. ID: {model_request_id}. Please wait for admin approval before submitting price."
            )
    else:
        raise HTTPException(status_code=400, detail="Standard model ID or new model name required")
    
    # 3. Handle Proof
    proof_img_path = None
    if proof_type == "image" and file:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid file")
        
        # Check file extension
        allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp"]
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
        
        # Check file size using file.size if available, otherwise seek
        file_size = 0
        if hasattr(file, 'size'):
            file_size = file.size
        else:
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
        
        filename = f"{datetime.now().timestamp()}_{provider.name}.{file_ext}".replace(" ", "_")
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
        status=PriceStatus.pending
    )
    
    session.add(price_record)
    session.commit()
    session.refresh(price_record)
    
    return {
        "message": "Price submitted successfully",
        "id": price_record.id,
        "provider_id": provider.id,
        "provider_status": provider.status.value
    }

@router.get("/compare/{standard_model_id}")
async def compare_prices(
    standard_model_id: int,
    target_currency: str = Query("USD"),
    session: Session = Depends(get_session)
):
    """Compare prices across providers for a model."""
    rates = session.exec(select(CurrencyRate)).all()
    rate_map = {r.code: r.rate_to_usd for r in rates}
    rate_map["USD"] = 1.0
    
    if target_currency not in rate_map:
        raise HTTPException(status_code=400, detail="Target currency not supported")
        
    target_k = rate_map[target_currency]
    
    # Only show approved providers
    query = select(ModelPrice, Provider).join(Provider).where(
        ModelPrice.standard_model_id == standard_model_id,
        ModelPrice.status == PriceStatus.active,
        or_(
            Provider.status == ProviderStatus.approved,
            Provider.is_official == True
        )
    )
    results = session.exec(query).all()
    
    response = []
    for price, provider in results:
        src_rate = rate_map.get(price.currency, 1.0)
        
        price_in_usd = price.input_price / src_rate
        price_out_usd = price.output_price / src_rate
        
        final_in = price_in_usd * target_k
        final_out = price_out_usd * target_k
        
        response.append({
            "provider_name": provider.name,
            "provider_model_name": price.provider_model_name,
            "provider_score": provider.avg_score,
            "uptime": provider.uptime_rate,
            "original_currency": price.currency,
            "price_in": final_in,
            "price_out": final_out,
            "verified_at": price.verified_at.isoformat() if price.verified_at else None,
            "proof_type": price.proof_type,
            "proof_content": price.proof_content,
            "proof": price.proof_img_path
        })
        
    response.sort(key=lambda x: x["price_in"])
    return response

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
    session: Session = Depends(get_session)
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
            StandardModelRequest.status == "pending"
        )
    ).first()
    if pending:
        return {"message": "Model already requested", "request_id": pending.id}
    
    request = StandardModelRequest(
        requested_name=name,
        vendor=vendor,
        requester_id=current_user.id
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
    current_user: User = Depends(get_current_user)
):
    price = session.get(ModelPrice, price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")
        
    if current_user.role not in ["admin", "super_admin"] and price.submitter_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate prices if being updated
    if "input_price" in price_data:
        if price_data["input_price"] < 0:
            raise HTTPException(status_code=400, detail="Input price cannot be negative")
        price.input_price = price_data["input_price"]
    if "output_price" in price_data:
        if price_data["output_price"] < 0:
            raise HTTPException(status_code=400, detail="Output price cannot be negative")
        price.output_price = price_data["output_price"]
    if "currency" in price_data:
        price.currency = price_data["currency"]
        
    session.commit()
    return {"message": "Price updated"}

