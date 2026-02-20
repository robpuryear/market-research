import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse

from backend.report_engine import generator
from backend.models.reports import ReportJobStatus

router = APIRouter(prefix="/api/reports", tags=["reports"])

# In-memory job tracking
_jobs: dict[str, ReportJobStatus] = {}


def _get_report_by_id(report_id: str) -> Optional[dict]:
    index = generator._load_index()
    for r in index:
        if r.get("id") == report_id:
            return r
    return None


@router.get("/")
async def list_reports():
    """List all generated reports."""
    return generator._load_index()


@router.get("/view/{report_id}")
async def view_report(report_id: str):
    """Serve report HTML for iframe viewing."""
    report = _get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(report["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    with open(path) as f:
        html = f.read()
    # Inject Plotly CDN if not standalone
    if "<script src=\"https://cdn.plot.ly" not in html:
        html = html.replace("</head>", '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script></head>', 1)
    return HTMLResponse(content=html)


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """Download standalone report HTML."""
    report = _get_report_by_id(report_id)
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
    """Kick off async report generation. Returns job_id for polling."""
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
    """Poll report generation job status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """Delete a report by ID."""
    report = _get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Delete the file
    path = Path(report["path"])
    if path.exists():
        path.unlink()

    # Remove from index
    index = generator._load_index()
    index = [r for r in index if r.get("id") != report_id]
    generator._save_index(index)

    return {"status": "deleted", "report_id": report_id}
