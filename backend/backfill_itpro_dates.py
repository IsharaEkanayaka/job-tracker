"""Backfill missing ITPro publication dates.

Run with:
    python -m backend.backfill_itpro_dates
"""
from sqlalchemy import select

from backend.collectors.itpro_lk import ItProCollector
from backend.db.models import Job
from backend.db.session import SessionLocal, init_db


def backfill() -> int:
    init_db()
    jobs = ItProCollector().fetch()
    by_url = {raw.url: raw.posted_at for raw in jobs if raw.url and raw.posted_at}
    updated = 0

    with SessionLocal() as db:
        saved_jobs = db.scalars(
            select(Job).where(Job.source == "itpro", Job.posted_at.is_(None))
        ).all()
        for job in saved_jobs:
            posted_at = by_url.get(job.url)
            if posted_at is not None:
                job.posted_at = posted_at
                updated += 1
        db.commit()
    return updated


if __name__ == "__main__":
    print(f"Backfilled {backfill()} ITPro publication dates.")
