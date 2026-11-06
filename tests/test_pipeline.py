from sqlalchemy import select

from backend.collectors.base import BaseCollector, RawJob
from backend.collectors.remotive import RemotiveCollector
from backend.db.models import Job, ScrapeRun
from backend.pipeline import run_collector


class FakeCollector(BaseCollector):
    name = "fake"

    def fetch(self):
        return [
            RawJob(title="Python Developer", company="Acme", url="http://a", description="<p>Python, SQL</p>"),
            RawJob(title="python developer", company="ACME", url="http://b"),  # duplicate
            RawJob(title="Sales Manager", company="Globex", url="http://c"),
        ]


class BrokenCollector(BaseCollector):
    name = "broken"

    def fetch(self):
        raise RuntimeError("site down")


def test_pipeline_dedupes_and_flags(db):
    run = run_collector(db, FakeCollector())
    assert run.status == "ok" and run.jobs_found == 3 and run.jobs_new == 2
    jobs = db.scalars(select(Job)).all()
    assert {j.title: j.is_software for j in jobs} == {
        "Python Developer": True, "Sales Manager": False}


def test_pipeline_is_idempotent(db):
    run_collector(db, FakeCollector())
    run = run_collector(db, FakeCollector())
    assert run.jobs_new == 0


def test_failing_collector_is_logged_not_raised(db):
    run = run_collector(db, BrokenCollector())
    assert run.status == "failed" and "site down" in run.error
    assert db.scalar(select(ScrapeRun).where(ScrapeRun.source == "broken")) is not None


def test_remotive_parse():
    payload = {"jobs": [{
        "title": "Backend Engineer", "url": "https://remotive.com/x",
        "company_name": "Acme", "candidate_required_location": "Worldwide",
        "publication_date": "2026-01-05T10:00:00", "description": "<p>hi</p>",
    }]}
    jobs = RemotiveCollector.parse(payload)
    assert jobs[0].company == "Acme" and jobs[0].remote is True
    assert jobs[0].posted_at is not None
