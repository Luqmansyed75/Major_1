"""
fasapi/routes/thread_route.py
------------------------------
Thread management endpoints (all require JWT):

    GET    /threads                  — list all threads owned by the caller
    POST   /threads                  — create a new thread, returns thread_id
    DELETE /threads/{thread_id}      — delete a thread (and its DB row)
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from fasapi.core.deps import get_current_user
from fasapi.db.connection import get_conn
from fasapi.schemas.thread_schema import CreateThreadRequest, ThreadListResponse, ThreadOut

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /threads
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=ThreadListResponse,
    summary="List conversations",
    description="Returns all thread IDs and titles owned by the authenticated user.",
)
async def list_threads(user_id: str = Depends(get_current_user)):
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT thread_id, thread_title, created_at, updated_at
                FROM   user_threads
                WHERE  user_id = %s
                ORDER  BY updated_at DESC
                """,
                (user_id,),
            )
            rows = await cur.fetchall()

    threads = [
        ThreadOut(
            thread_id=row[0],
            thread_title=row[1],
            created_at=row[2],
            updated_at=row[3],
        )
        for row in rows
    ]
    return ThreadListResponse(threads=threads)


# ---------------------------------------------------------------------------
# POST /threads
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=ThreadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation",
    description=(
        "Creates a new thread row and returns the `thread_id`. "
        "Pass this `thread_id` to **POST /chat/ask** to start a conversation."
    ),
)
async def create_thread(
    payload: CreateThreadRequest,
    user_id: str = Depends(get_current_user),
):
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_threads (user_id, thread_title)
                VALUES (%s, %s)
                RETURNING thread_id, thread_title, created_at, updated_at
                """,
                (user_id, payload.thread_title),
            )
            row = await cur.fetchone()

    return ThreadOut(
        thread_id=row[0],
        thread_title=row[1],
        created_at=row[2],
        updated_at=row[3],
    )


# ---------------------------------------------------------------------------
# DELETE /threads/{thread_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
    description=(
        "Deletes the thread row. "
        "LangGraph checkpoint data (in the checkpoints tables) is **not** removed here — "
        "it will simply become orphaned. Add a separate cleanup step if needed."
    ),
)
async def delete_thread(
    thread_id: UUID,
    user_id: str = Depends(get_current_user),
):
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                DELETE FROM user_threads
                WHERE  thread_id = %s AND user_id = %s
                RETURNING thread_id
                """,
                (str(thread_id), user_id),
            )
            deleted = await cur.fetchone()

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or does not belong to you.",
        )
