"""
fasapi/routes/auth_route.py
----------------------------
Authentication endpoints:

    POST /auth/register  — create account, returns JWT
    POST /auth/login     — verify credentials, returns JWT
    GET  /auth/me        — return current user info (JWT required)
"""
from fastapi import APIRouter, Depends, HTTPException, status

from fasapi.core.deps import get_current_user
from fasapi.core.security import create_access_token, hash_password, verify_password
from fasapi.db.connection import get_conn
from fasapi.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers — raw SQL CRUD kept in the route file to stay simple
# ---------------------------------------------------------------------------

async def _get_user_by_email(email: str) -> dict | None:
    """Return a user row dict or None if not found."""
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, email, hashed_pw, created_at FROM users WHERE email = %s",
                (email,),
            )
            row = await cur.fetchone()
    if row is None:
        return None
    return {"id": row[0], "email": row[1], "hashed_pw": row[2], "created_at": row[3]}


async def _get_user_by_id(user_id: str) -> dict | None:
    """Return a user row dict or None if not found."""
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, email, hashed_pw, created_at FROM users WHERE id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
    if row is None:
        return None
    return {"id": row[0], "email": row[1], "hashed_pw": row[2], "created_at": row[3]}


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new account and returns a Bearer JWT token.",
)
async def register(payload: RegisterRequest):
    # Reject duplicate emails
    existing = await _get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    hashed = hash_password(payload.password)

    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO users (email, hashed_pw)
                VALUES (%s, %s)
                RETURNING id, email
                """,
                (payload.email, hashed),
            )
            row = await cur.fetchone()

    user_id, email = str(row[0]), row[1]
    token = create_access_token(user_id=user_id, email=email)
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Verify email + password, return a Bearer JWT token.",
)
async def login(payload: LoginRequest):
    user = await _get_user_by_email(payload.email)

    if not user or not verify_password(payload.password, user["hashed_pw"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=str(user["id"]), email=user["email"])
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user",
    description="Returns the profile of the authenticated user.",
)
async def me(user_id: str = Depends(get_current_user)):
    user = await _get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserOut(id=user["id"], email=user["email"], created_at=user["created_at"])
