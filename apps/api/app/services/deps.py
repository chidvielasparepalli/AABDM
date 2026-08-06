"""Service injection helpers.

Each router resolves its service via Depends, so handlers stay thin:
Router (transport) → Service (orchestration) → Repository (persistence).
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..tenancy import CurrentOrg


def service_dep(service_cls):
    def _make(db: Session = Depends(get_db), org_id: int = CurrentOrg):
        return service_cls(db, org_id)

    return _make
