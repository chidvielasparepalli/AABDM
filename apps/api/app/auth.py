"""Clerk JWT verification for FastAPI.

Verifies the `Authorization: Bearer <session token>` header against Clerk's
JWKS. Needs `CLERK_PUBLISHABLE_KEY` env var (the publishable key encodes the
instance JWKS URL). Zero extra SDK dependency beyond PyJWT + httpx.
"""
import base64
import os
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Request, status

PUBLISHABLE_KEY = os.environ.get("CLERK_PUBLISHABLE_KEY", "")

if not PUBLISHABLE_KEY or PUBLISHABLE_KEY.startswith("pk_test_YOUR"):
    raise RuntimeError(
        "CLERK_PUBLISHABLE_KEY must be set. Add it to apps/api/.env."
    )


def _frontend_api() -> str:
    # pk_live_/pk_test_<b64> — the b64 payload decodes to the instance
    # frontend API domain (e.g. `clerk.example.clerk.accounts.dev$`).
    payload = PUBLISHABLE_KEY.split("_")[-1]
    raw = base64.urlsafe_b64decode(payload + "===").decode()
    domain = raw.rstrip("$")
    return f"https://{domain}"


def _jwks_url() -> str:
    return f"{_frontend_api()}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def _jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(_jwks_url())


def verify_clerk_token(token: str) -> dict:
    try:
        key = _jwks_client().get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    claims = verify_clerk_token(token)
    return {"sub": claims["sub"], "claims": claims}


CurrentUser = Depends(get_current_user)
