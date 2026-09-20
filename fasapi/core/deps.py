"""
fasapi/core/deps.py
-------------------
FastAPI dependency that extracts and validates the JWT Bearer token,
then returns the caller's user_id as a plain string.

Usage in routes:
    @router.get("/protected")
    async def my_route(user_id: str = Depends(get_current_user)):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fasapi.core.security import decode_access_token

# HTTPBearer → Swagger shows a simple "Value" field where you paste the token.
# Much cleaner than OAuth2PasswordBearer for a JWT-only app.
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    Decode the Bearer JWT and return the user_id (UUID as string).
    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    payload = decode_access_token(credentials.credentials)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
