from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class ReportMeta(BaseModel):
    id: str
    type: Literal["daily", "analytics", "research", "scanner"]
    ticker: Optional[str] = None  # only for type="research"
    generated_at: datetime
    path: str
    file_size_kb: Optional[float] = None
    title: str


class ReportJobStatus(BaseModel):
    job_id: str
    report_type: Literal["daily", "analytics", "research", "scanner"]
    ticker: Optional[str] = None
    status: Literal["pending", "running", "complete", "error"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    report_id: Optional[str] = None  # set when complete


class SchedulerJobInfo(BaseModel):
    id: str
    name: str
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    status: str  # "scheduled" | "running" | "paused"
