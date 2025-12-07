import json
import secrets
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
import pyotp
from app.database import get_session
from app.models import User, SystemSetting, EmailVerificationToken
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
)
from app.services.email import send_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).lower() in {"1", "true", "yes", "on"}


def _get_setting(session: Session, key: str, default: str | None = None) -> str | None:
    setting = session.get(SystemSetting, key)
    return setting.value if setting else default

@router.post("/register")
async def register(
    email: str, 
    password: str, 
    session: Session = Depends(get_session)
):
    # Check existing
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Determine role and email verification policy
    first_user = session.exec(select(User)).first()
    role = "super_admin" if not first_user else "user"
    force_email_verification = _truthy(_get_setting(session, "force_email_verification", "false"))

    # First super admin should not be blocked by verification
    email_verified = True if role == "super_admin" else not force_email_verification

    new_user = User(
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        email_verified=email_verified
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    message = "User registered successfully"
    if force_email_verification and role != "super_admin":
        # Generate verification token
        token = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(hours=24)
        evt = EmailVerificationToken(token=token, user_id=new_user.id, expires_at=expires_at)
        session.add(evt)
        session.commit()

        site_name = _get_setting(session, "site_name", "LLM Price Hub") or "LLM Price Hub"
        verify_link = f"/verify-email?token={token}"
        email_body = f"Welcome to {site_name}!\n\nPlease verify your email by visiting: {verify_link}\nThis link expires in 24 hours."
        send_email(email, f"Verify your email for {site_name}", email_body, session)
        message = "User registered, verification email sent"

    return {"message": message, "email_verified": email_verified}

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: str | None = Form(None),
    session: Session = Depends(get_session)
):
    # form_data.username is email
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    force_email_verification = _truthy(_get_setting(session, "force_email_verification", "false"))
    if force_email_verification and not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="EMAIL_NOT_VERIFIED")

    if user.totp_enabled:
        if not totp_code:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TOTP_REQUIRED")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(totp_code, valid_window=1):
            # Allow use of backup codes once
            backup_codes = json.loads(user.totp_backup_codes or "[]")
            if totp_code in backup_codes:
                backup_codes.remove(totp_code)
                user.totp_backup_codes = json.dumps(backup_codes)
                session.add(user)
                session.commit()
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOTP")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-email")
async def verify_email(token: str, session: Session = Depends(get_session)):
    evt = session.get(EmailVerificationToken, token)
    if not evt or evt.used or evt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = session.get(User, evt.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    evt.used = True
    session.add(user)
    session.add(evt)
    session.commit()
    return {"message": "Email verified"}


@router.post("/resend-verification")
async def resend_verification(email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified:
        return {"message": "Already verified"}

    token = uuid.uuid4().hex
    expires_at = datetime.utcnow() + timedelta(hours=24)
    evt = EmailVerificationToken(token=token, user_id=user.id, expires_at=expires_at)
    session.add(evt)
    session.commit()

    site_name = _get_setting(session, "site_name", "LLM Price Hub") or "LLM Price Hub"
    verify_link = f"/verify-email?token={token}"
    email_body = f"Hi, please verify your email by visiting: {verify_link}\nThe link expires in 24 hours."
    send_email(email, f"Verify your email for {site_name}", email_body, session)
    return {"message": "Verification email sent"}


@router.get("/totp/status")
async def totp_status(current_user: User = Depends(get_current_active_user)):
    return {
        "enabled": current_user.totp_enabled,
        "has_backup_codes": bool(json.loads(current_user.totp_backup_codes or "[]")),
        "email_verified": current_user.email_verified,
    }


@router.post("/totp/initiate")
async def totp_initiate(current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)):
    secret = pyotp.random_base32()
    current_user.totp_temp_secret = secret
    session.add(current_user)
    session.commit()

    issuer = _get_setting(session, "site_name", "LLM Price Hub") or "LLM Price Hub"
    uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name=issuer)
    return {"secret": secret, "otpauth_url": uri}


@router.post("/totp/activate")
async def totp_activate(code: str, current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)):
    if not current_user.totp_temp_secret:
        raise HTTPException(status_code=400, detail="No pending TOTP setup")

    totp = pyotp.TOTP(current_user.totp_temp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    backup_codes = [secrets.token_hex(4) for _ in range(6)]
    current_user.totp_secret = current_user.totp_temp_secret
    current_user.totp_temp_secret = None
    current_user.totp_enabled = True
    current_user.totp_backup_codes = json.dumps(backup_codes)
    session.add(current_user)
    session.commit()
    return {"message": "TOTP enabled", "backup_codes": backup_codes}


@router.post("/totp/disable")
async def totp_disable(code: str, current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)):
    if not current_user.totp_enabled or not current_user.totp_secret:
        return {"message": "TOTP not enabled"}

    totp = pyotp.TOTP(current_user.totp_secret)
    backup_codes = json.loads(current_user.totp_backup_codes or "[]")

    if not totp.verify(code, valid_window=1):
        if code in backup_codes:
            backup_codes.remove(code)
        else:
            raise HTTPException(status_code=400, detail="Invalid TOTP code")

    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_temp_secret = None
    current_user.totp_backup_codes = json.dumps(backup_codes)
    session.add(current_user)
    session.commit()
    return {"message": "TOTP disabled"}
