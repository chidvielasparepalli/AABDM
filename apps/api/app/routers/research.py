import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import SessionLocal, get_db
from ..domain.enums import ResearchStatus
from ..models import Client
from ..repositories import ResearchReportRepository
from ..research import run_research
from ..schemas import ResearchReportOut
from ..security.errors import SSrfBlocked
from ..security.ssrf import validate_url
from ..tenancy import CurrentOrg

router = APIRouter(prefix="/clients/{client_id}/research", tags=["research"])


def _get_client(db: Session, org_id: int, client_id: int) -> Client:
    from ..repositories import ClientRepository

    client = ClientRepository(db, org_id).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def _run_and_save(report_id: int, url: str, org_id: int) -> None:
    """Background: run research, persist result. Uses own session (thread)."""
    db = SessionLocal()
    try:
        repo = ResearchReportRepository(db, org_id)
        report = repo.get(report_id)
        if not report:
            return
        try:
            result = asyncio.run(run_research(url))
            for k, v in result.items():
                setattr(report, k, v)
        except Exception as exc:  # noqa: BLE001 — persist any failure
            report.status = ResearchStatus.ERROR
            report.error = str(exc)
        db.commit()
    finally:
        db.close()


@router.post("", response_model=ResearchReportOut, status_code=201)
def start_research(
    client_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    client = _get_client(db, org_id, client_id)
    url = client.website
    if not url:
        raise HTTPException(status_code=400, detail="Client has no website set")

    # Fail fast before spawning a background job: blocked URLs → 400,
    # not a 500 half-way through research.
    try:
        validate_url(url)
    except SSrfBlocked as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = ResearchReportRepository(db, org_id)
    report = repo.create(client_id=client_id, url=url)
    db.commit()
    db.refresh(report)
    background.add_task(_run_and_save, report.id, url, org_id)
    return report


@router.get("", response_model=ResearchReportOut)
def latest_report(
    client_id: int,
    db: Session = Depends(get_db),
    _: dict = CurrentUser,
    org_id: int = CurrentOrg,
):
    _get_client(db, org_id, client_id)
    report = ResearchReportRepository(db, org_id).latest(client_id)
    if not report:
        raise HTTPException(status_code=404, detail="No research report yet")
    return report
