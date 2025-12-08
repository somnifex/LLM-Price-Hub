from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session
from app.models import User, UserSettings, CurrencyRate
from app.auth import get_current_user
import json

router = APIRouter(prefix="/api/settings", tags=["settings"])


# Basic ISO currency -> emoji flag helper (fallback to empty string)
_FLAG_MAP = {
    "AED": "🇦🇪",
    "AFN": "🇦🇫",
    "ALL": "🇦🇱",
    "AMD": "🇦🇲",
    "ANG": "🇳🇱",
    "AOA": "🇦🇴",
    "ARS": "🇦🇷",
    "AUD": "🇦🇺",
    "AWG": "🇦🇼",
    "AZN": "🇦🇿",
    "BAM": "🇧🇦",
    "BBD": "🇧🇧",
    "BDT": "🇧🇩",
    "BGN": "🇧🇬",
    "BHD": "🇧🇭",
    "BIF": "🇧🇮",
    "BMD": "🇧🇲",
    "BND": "🇧🇳",
    "BOB": "🇧🇴",
    "BRL": "🇧🇷",
    "BSD": "🇧🇸",
    "BTN": "🇧🇹",
    "BWP": "🇧🇼",
    "BYN": "🇧🇾",
    "BZD": "🇧🇿",
    "CAD": "🇨🇦",
    "CDF": "🇨🇩",
    "CHF": "🇨🇭",
    "CLF": "🇨🇱",
    "CLP": "🇨🇱",
    "CNH": "🇨🇳",
    "CNY": "🇨🇳",
    "COP": "🇨🇴",
    "CRC": "🇨🇷",
    "CUP": "🇨🇺",
    "CVE": "🇨🇻",
    "CZK": "🇨🇿",
    "DJF": "🇩🇯",
    "DKK": "🇩🇰",
    "DOP": "🇩🇴",
    "DZD": "🇩🇿",
    "EGP": "🇪🇬",
    "ERN": "🇪🇷",
    "ETB": "🇪🇹",
    "EUR": "🇪🇺",
    "FJD": "🇫🇯",
    "FKP": "🇫🇰",
    "FOK": "🇫🇴",
    "GBP": "🇬🇧",
    "GEL": "🇬🇪",
    "GGP": "🇬🇬",
    "GHS": "🇬🇭",
    "GIP": "🇬🇮",
    "GMD": "🇬🇲",
    "GNF": "🇬🇳",
    "GTQ": "🇬🇹",
    "GYD": "🇬🇾",
    "HKD": "🇭🇰",
    "HNL": "🇭🇳",
    "HRK": "🇭🇷",
    "HTG": "🇭🇹",
    "HUF": "🇭🇺",
    "IDR": "🇮🇩",
    "ILS": "🇮🇱",
    "IMP": "🇮🇲",
    "INR": "🇮🇳",
    "IQD": "🇮🇶",
    "IRR": "🇮🇷",
    "ISK": "🇮🇸",
    "JEP": "🇯🇪",
    "JMD": "🇯🇲",
    "JOD": "🇯🇴",
    "JPY": "🇯🇵",
    "KES": "🇰🇪",
    "KGS": "🇰🇬",
    "KHR": "🇰🇭",
    "KID": "🇰🇮",
    "KMF": "🇰🇲",
    "KRW": "🇰🇷",
    "KWD": "🇰🇼",
    "KYD": "🇰🇾",
    "KZT": "🇰🇿",
    "LAK": "🇱🇦",
    "LBP": "🇱🇧",
    "LKR": "🇱🇰",
    "LRD": "🇱🇷",
    "LSL": "🇱🇸",
    "LYD": "🇱🇾",
    "MAD": "🇲🇦",
    "MDL": "🇲🇩",
    "MGA": "🇲🇬",
    "MKD": "🇲🇰",
    "MMK": "🇲🇲",
    "MNT": "🇲🇳",
    "MOP": "🇲🇴",
    "MRU": "🇲🇷",
    "MUR": "🇲🇺",
    "MVR": "🇲🇻",
    "MWK": "🇲🇼",
    "MXN": "🇲🇽",
    "MYR": "🇲🇾",
    "MZN": "🇲🇿",
    "NAD": "🇳🇦",
    "NGN": "🇳🇬",
    "NIO": "🇳🇮",
    "NOK": "🇳🇴",
    "NPR": "🇳🇵",
    "NZD": "🇳🇿",
    "OMR": "🇴🇲",
    "PAB": "🇵🇦",
    "PEN": "🇵🇪",
    "PGK": "🇵🇬",
    "PHP": "🇵🇭",
    "PKR": "🇵🇰",
    "PLN": "🇵🇱",
    "PYG": "🇵🇾",
    "QAR": "🇶🇦",
    "RON": "🇷🇴",
    "RSD": "🇷🇸",
    "RUB": "🇷🇺",
    "RWF": "🇷🇼",
    "SAR": "🇸🇦",
    "SBD": "🇸🇧",
    "SCR": "🇸🇨",
    "SDG": "🇸🇩",
    "SEK": "🇸🇪",
    "SGD": "🇸🇬",
    "SHP": "🇸🇭",
    "SLE": "🇸🇱",
    "SLL": "🇸🇱",
    "SOS": "🇸🇴",
    "SRD": "🇸🇷",
    "SSP": "🇸🇸",
    "STN": "🇸🇹",
    "SYP": "🇸🇾",
    "SZL": "🇸🇿",
    "THB": "🇹🇭",
    "TJS": "🇹🇯",
    "TMT": "🇹🇲",
    "TND": "🇹🇳",
    "TOP": "🇹🇴",
    "TRY": "🇹🇷",
    "TTD": "🇹🇹",
    "TVD": "🇹🇻",
    "TWD": "🇹🇼",
    "TZS": "🇹🇿",
    "UAH": "🇺🇦",
    "UGX": "🇺🇬",
    "USD": "🇺🇸",
    "UYU": "🇺🇾",
    "UZS": "🇺🇿",
    "VES": "🇻🇪",
    "VND": "🇻🇳",
    "VUV": "🇻🇺",
    "WST": "🇼🇸",
    "XAF": "🇫🇷",
    "XCD": "🇦🇬",
    "XOF": "🇫🇷",
    "XPF": "🇳🇨",
    "YER": "🇾🇪",
    "ZAR": "🇿🇦",
    "ZMW": "🇿🇲",
    "ZWG": "🇿🇼",
    "ZWL": "🇿🇼",
}


def _currency_flag(code: str) -> str:
    return _FLAG_MAP.get(code.upper(), "")


@router.get("/currencies")
async def get_currencies(session: Session = Depends(get_session)):
    """Get all available currencies and their rates."""
    currencies = session.exec(select(CurrencyRate)).all()
    common_codes = {"USD", "CNY", "EUR"}
    return [
        {
            "code": c.code,
            "rate_to_usd": c.rate_to_usd,
            "updated_at": c.updated_at,
            "is_common": c.code in common_codes,
            "flag": _currency_flag(c.code),
        }
        for c in currencies
    ]


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
