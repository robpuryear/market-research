from fastapi import APIRouter, HTTPException
from backend.models.reports import SchedulerJobInfo

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """Return status of all scheduled jobs."""
    try:
        from backend.core.scheduler import get_job_info
        return get_job_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
