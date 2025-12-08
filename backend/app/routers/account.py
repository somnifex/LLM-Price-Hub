import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import pyotp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.auth import get_current_active_user, get_password_hash
from app.database import get_session
from app.models import (
    EmailVerificationToken,
    SystemSetting,
    User,
    UserActionToken,
    UserSettings,
)
from app.services.email import send_email

router = APIRouter(prefix="/api/account", tags=["account"])

CODE_TTL_MINUTES = 15


class ActionCodeRequest(BaseModel):
    action: str
    new_email: Optional[EmailStr] = None


class PasswordResetRequest(BaseModel):
    new_password: str
    code: Optional[str] = None
    totp_code: Optional[str] = None


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
    code: Optional[str] = None
    totp_code: Optional[str] = None


def _site_name(session: Session) -> str:
    setting = session.get(SystemSetting, "site_name")
    return setting.value if setting else "LLM Price Hub"


def _verify_totp_or_backup(user: User, code: str, session: Session) -> bool:
    settings: Optional[UserSettings] = user.settings
    if not settings or not settings.totp_enabled or not settings.totp_secret:
        return False

    totp = pyotp.TOTP(settings.totp_secret)
    if totp.verify(code, valid_window=1):
        return True

    backup_codes = json.loads(settings.totp_backup_codes or "[]")
    if code in backup_codes:
        backup_codes.remove(code)
        settings.totp_backup_codes = json.dumps(backup_codes)
        session.add(settings)
        session.commit()
        return True
    return False


def _issue_action_code(
    session: Session, user: User, action: str, new_email: Optional[str] = None
) -> str:
    if action not in {"password_reset", "email_change"}:
        raise HTTPException(status_code=400, detail="INVALID_ACTION")

    # Invalidate older codes for the same action
    existing = session.exec(
        select(UserActionToken).where(
            UserActionToken.user_id == user.id,
            UserActionToken.action == action,
            UserActionToken.used == False,  # noqa: E712
        )
    ).all()
    for token in existing:
        token.used = True
        session.add(token)
    session.commit()

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=CODE_TTL_MINUTES)
    action_token = UserActionToken(
        token=code,
        user_id=user.id,
        action=action,
        new_email=new_email.lower() if new_email else None,
        expires_at=expires_at,
    )
    session.add(action_token)
    session.commit()
    return code


def _consume_action_code(
    session: Session,
    user: User,
    action: str,
    code: str,
    expected_email: Optional[str] = None,
) -> None:
    record = session.get(UserActionToken, code)
    if (
        not record
        or record.used
        or record.user_id != user.id
        or record.action != action
    ):
        raise HTTPException(status_code=400, detail="INVALID_CODE")

    if record.expires_at < datetime.utcnow():
        record.used = True
        session.add(record)
        session.commit()
        raise HTTPException(status_code=400, detail="CODE_EXPIRED")

    if expected_email and record.new_email:
        if record.new_email.lower() != expected_email.lower():
            raise HTTPException(status_code=400, detail="CODE_EMAIL_MISMATCH")

    record.used = True
    session.add(record)
    session.commit()


def _send_verification_email(session: Session, user: User) -> None:
    token = uuid.uuid4().hex
    expires_at = datetime.utcnow() + timedelta(hours=24)
    evt = EmailVerificationToken(token=token, user_id=user.id, expires_at=expires_at)
    session.add(evt)
    session.commit()

    site_name = _site_name(session)
    verify_link = f"/verify-email?token={token}"
    body = (
        f"Hi,\n\nPlease verify your email for {site_name} by visiting: {verify_link}\n"
        "This link expires in 24 hours."
    )
    send_email(user.email, f"Verify your email for {site_name}", body, session)


@router.post("/request-code")
async def request_action_code(
    req: ActionCodeRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    action = req.action
    new_email: Optional[str] = None
    target_email = current_user.email

    if action == "email_change":
        if not req.new_email:
            raise HTTPException(status_code=400, detail="NEW_EMAIL_REQUIRED")
        new_email = req.new_email.lower()
        if new_email == current_user.email:
            raise HTTPException(status_code=400, detail="EMAIL_UNCHANGED")
        conflict = session.exec(select(User).where(User.email == new_email)).first()
        if conflict:
            raise HTTPException(status_code=400, detail="EMAIL_TAKEN")
        target_email = new_email
    elif action != "password_reset":
        raise HTTPException(status_code=400, detail="INVALID_ACTION")

    code = _issue_action_code(session, current_user, action, new_email)
    site_name = _site_name(session)
    action_label = "Reset your password" if action == "password_reset" else "Confirm your new email"
    body = (
        f"{action_label} for {site_name}\n\n"
        f"Use this code within {CODE_TTL_MINUTES} minutes: {code}\n"
        "If you did not request this, please ignore it."
    )
    sent = send_email(target_email, f"{site_name} verification code", body, session)
    if not sent:
        raise HTTPException(status_code=500, detail="EMAIL_NOT_CONFIGURED")

    return {"message": "Code sent"}


@router.post("/reset-password")
async def reset_password(
    req: PasswordResetRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="PASSWORD_TOO_SHORT")

    verified = False
    if req.totp_code:
        verified = _verify_totp_or_backup(current_user, req.totp_code, session)
        if not verified:
            raise HTTPException(status_code=400, detail="INVALID_TOTP")

    if req.code and not verified:
        _consume_action_code(session, current_user, "password_reset", req.code)
        verified = True

    if not verified:
        raise HTTPException(status_code=400, detail="VERIFICATION_REQUIRED")

    current_user.password_hash = get_password_hash(req.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password updated"}


@router.post("/change-email")
async def change_email(
    req: EmailChangeRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    new_email = req.new_email.lower()
    if new_email == current_user.email:
        raise HTTPException(status_code=400, detail="EMAIL_UNCHANGED")

    conflict = session.exec(select(User).where(User.email == new_email)).first()
    if conflict:
        raise HTTPException(status_code=400, detail="EMAIL_TAKEN")

    verified = False
    verified_via_email = False

    if req.totp_code:
        verified = _verify_totp_or_backup(current_user, req.totp_code, session)
        if not verified:
            raise HTTPException(status_code=400, detail="INVALID_TOTP")

    if req.code and not verified:
        _consume_action_code(
            session, current_user, "email_change", req.code, expected_email=new_email
        )
        verified = True
        verified_via_email = True

    if not verified:
        raise HTTPException(status_code=400, detail="VERIFICATION_REQUIRED")

    current_user.email = new_email
    current_user.email_verified = verified_via_email
    session.add(current_user)
    session.commit()

    if not verified_via_email:
        _send_verification_email(session, current_user)

    return {"message": "Email updated", "email_verified": current_user.email_verified}
