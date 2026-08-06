"""Organization resolution and membership enforcement.

Multi-tenancy model: every business row carries `organization_id`. The
current organization is taken from the `X-Organization-ID` header and verified
against `organization_members`. Requests without the header fall back to the
legacy default organization (id 1) — the backward-compat path for existing
single-tenant installs and tests.

Trade-off: header-based (not the Clerk `org_id` JWT claim) keeps the backend
self-contained and testable. Clerk Organizations can later feed the same
dependency. The no-header fallback is a migration convenience: real
multi-tenant deployments must always send the header; it defaults to the
legacy org so nothing breaks during rollout.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .auth import CurrentUser
from .db import get_db
from .models import OrganizationMember

DEFAULT_ORG_ID = 1


def get_current_org(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = CurrentUser,
) -> int:
    """Resolve the active organization for this request.

    Header present  -> membership-checked, 403 on non-member.
    Header absent   -> legacy default org (backward compat).
    """
    raw = request.headers.get("X-Organization-ID")
    if raw is None:
        return DEFAULT_ORG_ID

    try:
        org_id = int(raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID must be an integer",
        ) from None

    is_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user["sub"],
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    return org_id


CurrentOrg = Depends(get_current_org)
