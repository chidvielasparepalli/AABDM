from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..domain.enums import MemorySource
from ..memory import extract_memories
from ..repositories import ClientRepository, MemoryRepository
from ..schemas import MemoryOut
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/clients/{client_id}/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
def list_memories(
    client_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return MemoryRepository(db, org_id).list_for_client(client_id, limit, offset)


def extract_from_call(db: Session, org_id: int, call_id: int) -> None:
    """After a call completes, extract and store new memories."""
    from ..repositories import CallRepository

    call = CallRepository(db, org_id).get(call_id)
    if not call or not call.transcript:
        return

    repo = MemoryRepository(db, org_id)
    existing = {
        m.value.lower() for m in repo.all_for_client(call.client_id)
    }
    client_lines = [t.text for t in call.transcript if t.role == "client"]
    ai_lines = [t.text for t in call.transcript if t.role == "ai"]
    facts = extract_memories(existing, client_lines, ai_lines)
    for key, value in facts:
        repo.create_from_call(call.client_id, key, value, MemorySource.CALL)
    db.commit()
