import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.collectors.base import BaseCollector, RawJob
from backend.db.models import Job, ScrapeRun
from backend.processing.dedupe import dedupe_hash
from backend.processing.filter import score_job
from backend.processing.normalizer import clean, strip_html

log = logging.getLogger(__name__)


def save_raw_job(db: Session, raw: RawJob, source: str) -> Job | None:
    """Normalize, score, dedupe and store one job. Returns None if duplicate."""
    title = clean(raw.title)
    company = clean(raw.company)
    location = clean(raw.location)
    if not title:
        return None

    if raw.url:
        existing = db.scalar(
            select(Job).where(Job.source == source, Job.url == raw.url)
        )
        if existing:
            if raw.posted_at and not existing.posted_at:
                existing.posted_at = raw.posted_at
            if location and not existing.location:
                existing.location = location
            if company and not existing.company:
                existing.company = company
            if raw.description and not existing.description:
                existing.description = strip_html(raw.description)
            return None

    h = dedupe_hash(title, company, location)
    if db.scalar(select(Job.id).where(Job.dedupe_hash == h)):
        return None

    description = strip_html(raw.description)
    is_software, score = score_job(title, description)
    job = Job(
        title=title, company=company, location=location, remote=raw.remote,
        description=description, url=raw.url, source=source,
        posted_at=raw.posted_at, is_software=is_software, score=score,
        dedupe_hash=h,
    )
    db.add(job)
    db.flush()
    return job


def run_collector(
    db: Session,
    collector: BaseCollector,
) -> ScrapeRun:
    """Run one collector. A failure is logged in scrape_runs and never raised,
    so one broken source can't break the others."""
    run = ScrapeRun(source=collector.name)
    db.add(run)
    db.commit()
    try:
        raw_jobs = collector.fetch()
        run.jobs_found = len(raw_jobs)
        new = 0
        for raw in raw_jobs:
            if save_raw_job(db, raw, collector.name):
                new += 1
        run.jobs_new = new
        run.status = "ok"
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        log.exception("Collector %s failed", collector.name)
        run.status = "failed"
        run.error = str(exc)[:1000]
        db.add(run)
        db.commit()
    return run


def run_all(
    db: Session,
    collectors: list[BaseCollector],
) -> list[ScrapeRun]:
    return [run_collector(db, c) for c in collectors]
