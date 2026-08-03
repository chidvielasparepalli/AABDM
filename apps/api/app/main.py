from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import CurrentUser
from .db import Base, engine
from .routers import analytics, bi, calendar, calls, clients, followups, learning, memory, negotiation, research

# ponytail: create_all on boot, fine for dev; Alembic migrations when schema stabilizes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AABDM API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}


@app.get("/me")
async def me(user: dict = CurrentUser):
    """Return the authenticated Clerk user's identity."""
    return {"userId": user["sub"]}
