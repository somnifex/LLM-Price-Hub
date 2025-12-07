"""JWT token utilities for authentication."""
from jose import JWTError, jwt
from app.auth import SECRET_KEY, ALGORITHM
from typing import Optional

def decode_jwt_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Returns:
        dict with token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
