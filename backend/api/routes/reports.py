import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from report_engine import generator
from models.reports import ReportJobStatus
from db.session import get_session

router = APIRouter(prefix="/api/reports", tags=["reports"])

# In-memory job tracking
_jobs: dict[str, ReportJobStatus] = {}


@router.get("/")
async def list_reports(session: AsyncSession = Depends(get_session)):
    """List all generated reports."""
    return await generator._load_index_db(session)


@router.get("/view/{report_id}")
async def view_report(report_id: str, session: AsyncSession = Depends(get_session)):
    """Serve report HTML for iframe viewing."""
    index = await generator._load_index_db(session)
    report = next((r for r in index if r.get("id") == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(report["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    with open(path) as f:
        html = f.read()
    if '<script src="https://cdn.plot.ly' not in html:
        html = html.replace(
            "</head>",
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script></head>',
            1,
        )
    return HTMLResponse(content=html)


@router.get("/download/{report_id}")
async def download_report(report_id: str, session: AsyncSession = Depends(get_session)):
    """Download standalone report HTML."""
    index = await generator._load_index_db(session)
    report = next((r for r in index if r.get("id") == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(report["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        path=str(path),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={path.name}"},
    )


async def _run_report_job(job_id: str, report_type: str, ticker: Optional[str] = None):
    job = _jobs[job_id]
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    try:
        if report_type == "daily":
            meta = await generator.generate_report_a(standalone=True)
        elif report_type == "analytics":
            meta = await generator.generate_report_b(standalone=True)
        elif report_type == "scanner":
            meta = await generator.generate_scanner_report(standalone=True)
        elif report_type == "research" and ticker:
            meta = await generator.generate_report_c(ticker.upper(), standalone=True)
        else:
            raise ValueError(f"Invalid report type: {report_type}")
        job.status = "complete"
        job.completed_at = datetime.now(timezone.utc)
        job.report_id = meta.id
    except Exception as e:
        job.status = "error"
        job.error = str(e)
        job.completed_at = datetime.now(timezone.utc)


@router.post("/generate/{report_type}")
async def generate_report(
    report_type: str,
    background_tasks: BackgroundTasks,
    ticker: Optional[str] = None,
):
    if report_type not in ("daily", "analytics", "research", "scanner"):
        raise HTTPException(status_code=400, detail="report_type must be daily, analytics, research, or scanner")
    if report_type == "research" and not ticker:
        raise HTTPException(status_code=400, detail="ticker required for research reports")

    job_id = str(uuid.uuid4())[:12]
    job = ReportJobStatus(
        job_id=job_id,
        report_type=report_type,
        ticker=ticker.upper() if ticker else None,
        status="pending",
    )
    _jobs[job_id] = job
    background_tasks.add_task(_run_report_job, job_id, report_type, ticker)
    return {"job_id": job_id, "status": "pending"}


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{report_id}")
async def delete_report(report_id: str, session: AsyncSession = Depends(get_session)):
    index = await generator._load_index_db(session)
    report = next((r for r in index if r.get("id") == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    path = Path(report["path"])
    if path.exists():
        path.unlink()

    await generator._delete_report_db(session, report_id)
    return {"status": "deleted", "report_id": report_id}
