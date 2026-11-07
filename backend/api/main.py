from contextlib import asynccontextmanager
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.schemas import ApplicationIn, JobOut, ManualJobIn
from backend.collectors import ALL_COLLECTORS
from backend.collectors.base import RawJob
from backend.db.models import Application, Job
from backend.db.session import get_db, init_db
from backend.pipeline import run_all, save_raw_job

VALID_STATUSES = {"saved", "applied", "interview", "rejected", "offer", "skipped"}
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Job Tracker", lifespan=lifespan)


# Serves the built React app (run `npm run build` in /frontend). During development
# you use the Vite dev server on :5173 instead, which proxies API calls here.
app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets", check_dir=False), name="assets")


@app.get("/", include_in_schema=False)
def index():
    page = FRONTEND_DIST / "index.html"
    if page.exists():
        return FileResponse(page)
    return HTMLResponse(
        "<h1>Job Tracker API</h1>"
        "<p>The UI is not built yet. Run <code>npm run build</code> in the "
        "<code>frontend</code> folder, or use <code>npm run dev</code> and open "
        "<a href='http://localhost:5173'>localhost:5173</a>. "
        "API docs: <a href='/docs'>/docs</a>.</p>"
    )


@app.get("/jobs", response_model=list[JobOut])
def list_jobs(
    q: str | None = None,
    source: str | None = None,
    software_only: bool = True,
    remote: bool | None = None,
    status: str | None = Query(None, description="none | any | saved | applied | ..."),
    posted_from: date | None = Query(None, description="Published on or after this date"),
    posted_to: date | None = Query(None, description="Published on or before this date"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = select(Job)
    if software_only:
        stmt = stmt.where(Job.is_software.is_(True))
    if source:
        stmt = stmt.where(Job.source == source)
    if remote is not None:
        stmt = stmt.where(Job.remote.is_(remote))
    if status == "none":
        stmt = stmt.where(~Job.application.has())
    elif status == "any":
        stmt = stmt.where(Job.application.has())
    elif status:
        stmt = stmt.where(Job.application.has(Application.status == status))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Job.title.ilike(like) | Job.company.ilike(like))
    if posted_from and posted_to and posted_from > posted_to:
        raise HTTPException(422, "posted_from must be on or before posted_to")
    if posted_from:
        stmt = stmt.where(Job.posted_at >= datetime.combine(posted_from, time.min))
    if posted_to:
        stmt = stmt.where(
            Job.posted_at < datetime.combine(posted_to + timedelta(days=1), time.min)
        )
    # Newest first by the job's own posted date (falls back to when we fetched it).
    stmt = stmt.order_by(
        func.coalesce(Job.posted_at, Job.fetched_at).desc(), Job.id.desc()
    ).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@app.post("/jobs/manual", response_model=JobOut, status_code=201)
def add_manual_job(body: ManualJobIn, db: Session = Depends(get_db)):
    raw = RawJob(title=body.title, url=body.url, company=body.company,
                 location=body.location, description=body.description)
    job = save_raw_job(db, raw, body.source)
    if job is None:
        raise HTTPException(409, "Duplicate or invalid job")
    db.commit()
    return job


@app.put("/jobs/{job_id}/application", response_model=JobOut)
def set_application(job_id: int, body: ApplicationIn, db: Session = Depends(get_db)):
    if body.status not in VALID_STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(VALID_STATUSES)}")
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    app_row = job.application or Application(job_id=job.id)
    app_row.status = body.status
    app_row.notes = body.notes
    if body.status == "applied" and app_row.applied_at is None:
        app_row.applied_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(app_row)
    db.commit()
    db.refresh(job)
    return job


@app.delete("/jobs/{job_id}/application", response_model=JobOut)
def clear_application(job_id: int, db: Session = Depends(get_db)):
    """Put a job back to 'New' by removing its tracking record (and notes)."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.application:
        db.delete(job.application)
        db.commit()
        db.refresh(job)
    return job


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    per_source = dict(db.execute(
        select(Job.source, func.count()).where(Job.is_software.is_(True)).group_by(Job.source)
    ).all())
    per_status = dict(db.execute(
        select(Application.status, func.count()).group_by(Application.status)
    ).all())
    new_jobs = db.scalar(
        select(func.count()).select_from(Job)
        .where(Job.is_software.is_(True), ~Job.application.has())
    )
    sources = db.scalars(select(Job.source).distinct().order_by(Job.source)).all()
    return {
        "new_jobs": new_jobs,
        "sources": sources,
        "total_jobs": db.scalar(select(func.count()).select_from(Job)),
        "software_jobs": sum(per_source.values()),
        "jobs_per_source": per_source,
        "applications_per_status": per_status,
    }


@app.post("/collect/run")
def trigger_collect(db: Session = Depends(get_db)):
    runs = run_all(db, [c() for c in ALL_COLLECTORS])
    return [{"source": r.source, "status": r.status, "found": r.jobs_found,
             "new": r.jobs_new, "error": r.error} for r in runs]
