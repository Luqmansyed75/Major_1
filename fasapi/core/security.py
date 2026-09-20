"""
fasapi/core/security.py
-----------------------
Password hashing (bcrypt directly — no passlib) and JWT sign / verify.

Env vars read:
    JWT_SECRET       — signing key (required in production)
    JWT_EXPIRE_DAYS  — token lifetime in days (default: 7)
"""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
JWT_SECRET: str    = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

# ---------------------------------------------------------------------------
# Password hashing — bcrypt called directly (passlib is incompatible with
# bcrypt >= 4.x due to the removed __about__ attribute)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain* as a UTF-8 string."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* string."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, email: str) -> str:
    """
    Create a signed JWT containing the user's id and email.
    Expires after JWT_EXPIRE_DAYS days.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub":   str(user_id),
        "email": email,
        "exp":   expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT.
    Raises HTTP 401 on any failure (expired, tampered, missing sub).
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("sub") is None:
            raise credentials_error
        return payload
    except JWTError:
        raise credentials_error
