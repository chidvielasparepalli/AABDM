"""Application service base.

Services own orchestration, transactions, and domain-rule application.
They sit between transport (routers) and persistence (repositories).
Constructed per-request with the request-scoped session and resolved org.
"""

from sqlalchemy.orm import Session


class Service:
    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id
