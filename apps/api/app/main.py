import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .auth import CurrentUser
from .config import settings
from .exceptions import register_exception_handlers
from .logging import setup_logging
from .middleware import RequestContextMiddleware
from .routers import (
    analytics,
    bi,
    calendar,
    calls,
    clients,
    followups,
    learning,
    memory,
    negotiation,
    research,
)

setup_logging(settings.log_level)


def run_migrations() -> None:
    """Run alembic upgrade head on boot — idempotent."""
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_migrate:
        run_migrations()
    # Register event handlers (subscriptions) at startup
    from .events.handlers import register_handlers
    register_handlers()
    yield


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

# Rate limiting (in-memory storage — ponytail: Redis when scaling to multiple workers)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds} minute"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)

app.include_router(clients.router)
app.include_router(research.router)
app.include_router(bi.router)
app.include_router(calls.router)
app.include_router(negotiation.router)
app.include_router(calendar.router)
app.include_router(followups.router)
app.include_router(analytics.router)
app.include_router(memory.router)
app.include_router(learning.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.api_version}


@app.get("/me")
async def me(user: dict = CurrentUser):
    """Return the authenticated Clerk user's identity."""
    return {"userId": user["sub"]}
