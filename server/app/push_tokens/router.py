"""Push-token router (stores hashes only)."""

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.deps import Repos, get_current_user, get_repos
from app.core.security import hash_token_value
from app.push_tokens.schemas import PushTokenCreate, PushTokenPublic

router = APIRouter(prefix="/push-tokens", tags=["push-tokens"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Register push token")
async def register_token(body: PushTokenCreate, request: Request, user: dict = Depends(get_current_user)):
    repos: Repos = get_repos(request)
    row = await repos.push_tokens.upsert(
        user_id=str(user["id"]),
        token_hash=hash_token_value(body.token),
        platform=body.platform.value,
        token=body.token,
    )
    return {
        "id": row["id"],
        "platform": row["platform"],
        "created_at": row["created_at"],
        "last_seen_at": row["last_seen_at"],
    }


@router.get("", response_model=list[PushTokenPublic], summary="List my push tokens")
async def list_tokens(request: Request, user: dict = Depends(get_current_user)):
    repos: Repos = get_repos(request)
    rows = await repos.push_tokens.list_for_user(str(user["id"]))
    return [
        {
            "id": r["id"],
            "platform": r["platform"],
            "created_at": r["created_at"],
            "last_seen_at": r["last_seen_at"],
        }
        for r in rows
    ]


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a push token")
async def delete_token(
    request: Request,
    user: dict = Depends(get_current_user),
    token: str = Query(min_length=10, max_length=512),
):
    repos: Repos = get_repos(request)
    await repos.push_tokens.delete(str(user["id"]), hash_token_value(token))
    return None
