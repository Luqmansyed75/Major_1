"""
fasapi/routes/integrations_route.py
-------------------------------------
Endpoints for managing per-user Gmail and GitHub credentials.

All routes are JWT-protected via Depends(get_current_user).

    GET    /integrations/status          — check which services are connected
    POST   /integrations/github          — save / update GitHub PAT
    POST   /integrations/gmail           — save / update Gmail token JSON
    DELETE /integrations/{service}       — disconnect github or gmail
"""
from fastapi import APIRouter, Depends, HTTPException, status

from fasapi.core.deps import get_current_user
from fasapi.db.connection import get_conn
from fasapi.schemas.integrations_schema import (
    GithubTokenRequest,
    GmailTokenRequest,
    IntegrationStatusResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper — upsert a single column in user_credentials
# ---------------------------------------------------------------------------
async def _upsert_credential(user_id: str, column: str, value: str | None) -> None:
    """
    Insert or update the user_credentials row for `user_id`,
    setting `column` to `value`.  `column` must be a trusted internal string
    (never user-supplied) to avoid SQL injection.
    """
    allowed = {"github_token", "gmail_token_json"}
    if column not in allowed:
        raise ValueError(f"Invalid credential column: {column}")

    sql = f"""
        INSERT INTO user_credentials (user_id, {column}, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE
            SET {column}   = EXCLUDED.{column},
                updated_at = NOW()
    """
    async with get_conn() as conn:
        await conn.execute(sql, (user_id, value))


# ---------------------------------------------------------------------------
# GET /integrations/status
# ---------------------------------------------------------------------------
@router.get(
    "/status",
    response_model=IntegrationStatusResponse,
    summary="Check integration status",
    description="Returns which services (GitHub, Gmail) the authenticated user has connected.",
)
async def integration_status(user_id: str = Depends(get_current_user)):
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT github_token, gmail_token_json
                FROM   user_credentials
                WHERE  user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()

    if row is None:
        return IntegrationStatusResponse(github_connected=False, gmail_connected=False)

    return IntegrationStatusResponse(
        github_connected=bool(row[0]),
        gmail_connected=bool(row[1]),
    )


# ---------------------------------------------------------------------------
# POST /integrations/github
# ---------------------------------------------------------------------------
@router.post(
    "/github",
    status_code=status.HTTP_200_OK,
    summary="Save GitHub Personal Access Token",
    description=(
        "Stores (or replaces) the GitHub PAT for the authenticated user. "
        "The agent will use this token for all GitHub MCP tool calls."
    ),
)
async def save_github_token(
    payload: GithubTokenRequest,
    user_id: str = Depends(get_current_user),
):
    if not payload.github_token.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="github_token cannot be empty.",
        )
    await _upsert_credential(user_id, "github_token", payload.github_token.strip())
    return {"message": "GitHub token saved successfully."}


# ---------------------------------------------------------------------------
# POST /integrations/gmail
# ---------------------------------------------------------------------------
@router.post(
    "/gmail",
    status_code=status.HTTP_200_OK,
    summary="Save Gmail OAuth token JSON",
    description=(
        "Stores (or replaces) the Gmail OAuth token JSON for the authenticated user. "
        "Paste the full contents of your local token.json file. "
        "The agent will use this to authenticate Gmail MCP tool calls."
    ),
)
async def save_gmail_token(
    payload: GmailTokenRequest,
    user_id: str = Depends(get_current_user),
):
    import json as _json

    # Validate that it's parseable JSON
    try:
        _json.loads(payload.gmail_token_json)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="gmail_token_json must be valid JSON.",
        )

    await _upsert_credential(user_id, "gmail_token_json", payload.gmail_token_json.strip())
    return {"message": "Gmail token saved successfully."}


# ---------------------------------------------------------------------------
# DELETE /integrations/{service}
# ---------------------------------------------------------------------------
@router.delete(
    "/{service}",
    status_code=status.HTTP_200_OK,
    summary="Disconnect a service",
    description="Clears the stored token for 'github' or 'gmail'.",
)
async def disconnect_integration(
    service: str,
    user_id: str = Depends(get_current_user),
):
    service_map = {
        "github": "github_token",
        "gmail":  "gmail_token_json",
    }
    column = service_map.get(service.lower())
    if not column:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown service '{service}'. Valid values: github, gmail.",
        )

    await _upsert_credential(user_id, column, None)
    return {"message": f"{service.capitalize()} disconnected successfully."}
