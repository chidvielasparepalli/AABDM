import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Client, ResearchReport
from ..research import run_research
from ..schemas import ResearchReportOut

router = APIRouter(prefix="/clients/{client_id}/research", tags=["research"])


def _get_client(client_id: int, db: Session) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def _run_and_save(report_id: int, url: str) -> None:
    """Background: run research, persist result. Uses own session (thread)."""
    from ..db import SessionLocal  # avoid import cycle

    db = SessionLocal()
    try:
        report = db.get(ResearchReport, report_id)
        if not report:
            return
        try:
            result = asyncio.run(run_research(url))
            for k, v in result.items():
                setattr(report, k, v)
        except Exception as exc:  # noqa: BLE001 — persist any failure
            report.status = "error"
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
):
    client = _get_client(client_id, db)
    url = client.website
    if not url:
        raise HTTPException(status_code=400, detail="Client has no website set")

    report = ResearchReport(client_id=client_id, url=url)
    db.add(report)
    db.commit()
    db.refresh(report)
    background.add_task(_run_and_save, report.id, url)
    return report


@router.get("", response_model=ResearchReportOut)
def latest_report(client_id: int, db: Session = Depends(get_db), _: dict = CurrentUser):
    _get_client(client_id, db)
    report = (
        db.query(ResearchReport)
        .filter(ResearchReport.client_id == client_id)
        .order_by(ResearchReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No research report yet")
    return report
