from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class PriceStatus(str, Enum):
    pending = "pending"
    active = "active"
    rejected = "rejected"
    expired = "expired"

class ProviderStatus(str, Enum):
    private = "private"      # Only visible to owner
    pending = "pending"      # Submitted for public review
    approved = "approved"    # Publicly visible
    rejected = "rejected"    # Review rejected

class CurrencyRate(SQLModel, table=True):
    __tablename__ = "currency_rates"
    code: str = Field(primary_key=True, max_length=10)
    rate_to_usd: float = Field(default=1.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Provider(SQLModel, table=True):
    __tablename__ = "providers"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    website: Optional[str] = Field(default=None, max_length=255)
    is_official: bool = Field(default=False)
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    status: ProviderStatus = Field(default=ProviderStatus.private)
    
    openai_base_url: Optional[str] = Field(default=None, max_length=500)
    gemini_base_url: Optional[str] = Field(default=None, max_length=500)
    claude_base_url: Optional[str] = Field(default=None, max_length=500)
    
    proof_type: Optional[str] = Field(default=None, max_length=20)
    proof_content: Optional[str] = Field(default=None, max_length=2000)
    
    avg_score: float = Field(default=0.0)
    uptime_rate: float = Field(default=100.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    prices: list["ModelPrice"] = Relationship(back_populates="provider")
    reviews: list["Review"] = Relationship(back_populates="provider")
    owner: Optional["User"] = Relationship(back_populates="private_providers")

class StandardModel(SQLModel, table=True):
    __tablename__ = "standard_models"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    vendor: Optional[str] = Field(default=None, max_length=50)

    prices: list["ModelPrice"] = Relationship(back_populates="standard_model")

class StandardModelRequest(SQLModel, table=True):
    """User requests for new standard model names to be added."""
    __tablename__ = "standard_model_requests"
    id: Optional[int] = Field(default=None, primary_key=True)
    requested_name: str = Field(max_length=100)
    vendor: Optional[str] = Field(default=None, max_length=50)
    requester_id: int = Field(foreign_key="users.id")
    status: str = Field(default="pending")  # pending/approved/rejected
    admin_notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    requester: Optional["User"] = Relationship(back_populates="model_requests")

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=100)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    email_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # TOTP 2FA
    totp_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = Field(default=None, max_length=64)
    totp_backup_codes: Optional[str] = Field(default=None, max_length=2000)  # JSON list
    totp_temp_secret: Optional[str] = Field(default=None, max_length=64)
    
    prices: list["ModelPrice"] = Relationship(back_populates="submitter")
    private_providers: list["Provider"] = Relationship(back_populates="owner")
    api_keys: list["UserAPIKey"] = Relationship(back_populates="user")
    settings: Optional["UserSettings"] = Relationship(back_populates="user")
    model_requests: list["StandardModelRequest"] = Relationship(back_populates="requester")


class EmailVerificationToken(SQLModel, table=True):
    __tablename__ = "email_verification_tokens"
    token: str = Field(primary_key=True, max_length=64)
    user_id: int = Field(foreign_key="users.id")
    expires_at: datetime = Field()
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship()

class SystemSetting(SQLModel, table=True):
    __tablename__ = "system_settings"
    key: str = Field(primary_key=True, max_length=50)
    value: str = Field(max_length=255)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ModelPrice(SQLModel, table=True):
    __tablename__ = "model_prices"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    provider_id: int = Field(foreign_key="providers.id")
    standard_model_id: int = Field(foreign_key="standard_models.id")
    submitter_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    # Provider's custom model name (may differ from standard name)
    provider_model_name: Optional[str] = Field(default=None, max_length=100)
    original_model_name: Optional[str] = Field(default=None, max_length=100)
    
    currency: str = Field(default="USD", max_length=10)
    input_price: float
    output_price: float
    
    # Flexible proof (image, text, or URL)
    proof_type: Optional[str] = Field(default=None, max_length=20)  # 'image', 'text', 'url'
    proof_content: Optional[str] = Field(default=None, max_length=2000)
    proof_img_path: Optional[str] = Field(default=None, max_length=255)  # Legacy, keep for compatibility
    
    status: PriceStatus = Field(default=PriceStatus.pending)
    verified_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    provider: Optional[Provider] = Relationship(back_populates="prices")
    standard_model: Optional[StandardModel] = Relationship(back_populates="prices")
    submitter: Optional[User] = Relationship(back_populates="prices")

class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="providers.id")
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    provider: Optional[Provider] = Relationship(back_populates="reviews")

class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    e2ee_enabled: bool = Field(default=False)
    e2ee_salt: Optional[str] = Field(default=None, max_length=255)
    e2ee_verification: Optional[str] = Field(default=None, max_length=500)
    
    user: Optional[User] = Relationship(back_populates="settings")

class UserAPIKey(SQLModel, table=True):
    __tablename__ = "user_api_keys"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    provider_id: int = Field(foreign_key="providers.id")
    api_key: str = Field(max_length=1000)
    is_encrypted: bool = Field(default=False)
    note: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="api_keys")
    provider: Optional[Provider] = Relationship()

