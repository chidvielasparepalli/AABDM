"""Generic org-scoped repository base.

Subclass sets `model`; instantiate with (db, org_id). All reads filter by
the org, all writes stamp it. This is the single place tenant scoping lives —
a repo that forgets `_base()` or `add()` is a bug visible on sight.
"""

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class ModelRepository(Generic[T]):
    model: type

    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id

    def _base(self):
        return self.db.query(self.model).filter(self.model.organization_id == self.org_id)

    def get(self, pk: int) -> T | None:
        return self._base().filter(self.model.id == pk).first()

    def add(self, **attrs) -> T:
        obj = self.model(organization_id=self.org_id, **attrs)
        self.db.add(obj)
        return obj

    def all(self) -> list[T]:
        return self._base().all()
