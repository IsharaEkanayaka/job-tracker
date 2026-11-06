"""Run collectors on a schedule:  python -m backend.scheduler"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from backend.collectors import ALL_COLLECTORS
from backend.db.session import SessionLocal, init_db
from backend.pipeline import run_all

logging.basicConfig(level=logging.INFO)


def job():
    with SessionLocal() as db:
        run_all(db, [c() for c in ALL_COLLECTORS])


if __name__ == "__main__":
    init_db()
    job()  # run once at startup
    sched = BlockingScheduler()
    sched.add_job(job, "interval", hours=6)
    sched.start()
