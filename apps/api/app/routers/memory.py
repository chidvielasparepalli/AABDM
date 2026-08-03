from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..memory import extract_memories
from ..models import Client, Memory, TranscriptLine
from ..schemas import MemoryOut

router = APIRouter(prefix="/clients/{client_id}/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
def list_memories(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return (
        db.query(Memory)
        .filter(Memory.client_id == client_id)
        .order_by(Memory.created_at.desc())
        .all()
    )


def extract_from_call(db: Session, call_id: int) -> None:
    """After a call completes, extract and store new memories."""
    from ..models import Call

    call = db.get(Call, call_id)
    if not call or not call.transcript:
        return

    existing = {
        m.value.lower() for m in db.query(Memory).filter(Memory.client_id == call.client_id).all()
    }
    client_lines = [t.text for t in call.transcript if t.role == "client"]
    ai_lines = [t.text for t in call.transcript if t.role == "ai"]
    facts = extract_memories(existing, client_lines, ai_lines)
    for key, value in facts:
        db.add(Memory(client_id=call.client_id, key=key, value=value, source="call"))
    db.commit()
