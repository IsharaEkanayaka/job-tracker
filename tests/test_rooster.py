import json

import httpx
import pytest
from sqlalchemy import select

from backend.collectors.base import BaseCollector
from backend.collectors.rooster import RoosterCollector
from backend.db.models import Job
from backend.pipeline import run_collector

# Shaped like the real Rooster search response (descriptions shortened).
SAMPLE = {
    "status": 200,
    "body": {
        "count": 4,
        "data": [
            {
                "id": 520040, "title": "Solutions Consultant",
                "description": "Presales role. Azure, APIs, integration.",
                "job_type": "full-time", "location": "Colombo, Sri Lanka",
                "created_at": "2026-11-02 09:57:06", "remote": False,
                "company_name": "Intiv (Pvt) Ltd", "subsidiary_company_name": None,
                "min_salary": 200000, "max_salary": 400000,
                "salary_frequency": "month", "salary_currency": "LKR",
            },
            {
                "id": 520059, "title": "Inventory Planning Analyst (Night Shift / Fully Remote)",
                "description": "Data entry and purchase orders.",
                "location": "Colombo, Sri Lanka", "created_at": "2026-11-04 06:18:13",
                "remote": True, "company_name": "Nextjob", "subsidiary_company_name": None,
                "min_salary": None, "max_salary": None,
            },
            {
                "id": 519931, "title": "Backend Developer",
                "description": "Build REST APIs with Python, PostgreSQL, Docker, AWS and Git.",
                "location": "Colombo, Sri Lanka", "created_at": "2026-11-05 09:00:00",
                "remote": False, "company_name": "Acme Holdings", "subsidiary_company_name": "Acme Labs",
                "min_salary": 800000, "max_salary": 800000,
                "salary_frequency": "month", "salary_currency": "LKR",
            },
            {"id": None, "title": "Broken record"},
        ],
    },
}


def test_parse_maps_fields():
    jobs = RoosterCollector.parse(SAMPLE)
    assert len(jobs) == 3  # record without id is skipped
    first = jobs[0]
    assert first.url == "https://rooster.jobs/jobs/520040"
    assert first.company == "Intiv (Pvt) Ltd"
    assert first.posted_at is not None
    assert first.description.startswith("Salary: LKR 200,000 - 400,000/month")
    assert jobs[1].remote is True
    assert jobs[2].company == "Acme Labs"  # subsidiary preferred
    assert "Salary: LKR 800,000/month" in jobs[2].description


def test_parse_rejects_unexpected_shape():
    with pytest.raises(ValueError):
        RoosterCollector.parse({"status": 200, "body": {"results": []}})


def test_pipeline_flags_software_jobs(db):
    class Fake(BaseCollector):
        name = "rooster"
        def fetch(self):
            return RoosterCollector.parse(SAMPLE)

    run = run_collector(db, Fake())
    assert run.status == "ok" and run.jobs_new == 3
    flags = {j.title: j.is_software for j in db.scalars(select(Job)).all()}
    assert flags["Backend Developer"] is True
    assert flags["Inventory Planning Analyst (Night Shift / Fully Remote)"] is False


def test_unconfigured_collector_fails_clearly():
    with pytest.raises(RuntimeError, match="ROOSTER_API_URL"):
        RoosterCollector(url="").fetch()


def _page(ids):
    return {"body": {"count": 99, "data": [
        {"id": i, "title": f"Developer {i}", "description": "Python", "company_name": "Co"} for i in ids]}}


def test_fetch_posts_page_and_limit_and_stops_on_short_page(monkeypatch):
    monkeypatch.setattr("backend.collectors.rooster.time.sleep", lambda s: None)
    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        body = json.loads(request.content)
        bodies.append(body)
        return httpx.Response(200, json=_page([1, 2] if body["page"] == 1 else [3]))

    c = RoosterCollector(url="https://api.example/search", extra={"keyword": "python"},
                         limit=2, max_pages=5, transport=httpx.MockTransport(handler))
    jobs = c.fetch()
    assert [j.url.rsplit("/", 1)[1] for j in jobs] == ["1", "2", "3"]
    assert bodies == [{"keyword": "python", "page": 1, "limit": 2},
                      {"keyword": "python", "page": 2, "limit": 2}]


def test_fetch_respects_max_pages(monkeypatch):
    monkeypatch.setattr("backend.collectors.rooster.time.sleep", lambda s: None)
    handler = lambda req: httpx.Response(200, json=_page([1, 2]))  # noqa: E731
    c = RoosterCollector(url="https://api.example/search", extra={}, limit=2, max_pages=3,
                         transport=httpx.MockTransport(handler))
    assert len(c.fetch()) == 6


def test_http_error_is_raised_for_pipeline_to_log():
    handler = lambda req: httpx.Response(400, json={"message": ["Page is required"]})  # noqa: E731
    c = RoosterCollector(url="https://api.example/search", extra={},
                         transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        c.fetch()


def test_bad_filters_config_is_reported():
    with pytest.raises(ValueError, match="ROOSTER_FILTERS"):
        RoosterCollector._load_filters("{not json")
    with pytest.raises(ValueError, match="JSON object"):
        RoosterCollector._load_filters("[1, 2]")


def test_default_body_comes_from_config(monkeypatch):
    monkeypatch.setattr("backend.collectors.rooster.ROOSTER_QUERY", ["python", "rust"])
    monkeypatch.setattr("backend.collectors.rooster.ROOSTER_FILTERS", '{"country": "Sri Lanka"}')
    c = RoosterCollector(url="https://api.example/search")
    assert c.extra == {"query": ["python", "rust"], "filters": {"country": "Sri Lanka"}}
