import json
import time
from datetime import datetime

import httpx

from backend.collectors.base import BaseCollector, RawJob
from backend.config import (
    REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT, ROOSTER_API_URL, ROOSTER_FILTERS,
    ROOSTER_LIMIT, ROOSTER_MAX_PAGES, ROOSTER_QUERY, USER_AGENT,
)

JOB_URL = "https://rooster.jobs/jobs/{id}"


class RoosterCollector(BaseCollector):
    """Rooster.jobs. POSTs to the JSON search endpoint the website itself uses.

    The body must contain integer `page` and `limit`; the search terms and filters
    come from ROOSTER_QUERY and ROOSTER_FILTERS (see config.py). This is not a documented public API,
    so it can change without notice: keep the schedule gentle and fail loudly if
    the response shape changes.
    """

    name = "rooster"

    def __init__(self, url: str = ROOSTER_API_URL, extra: dict | None = None,
                 limit: int = ROOSTER_LIMIT, max_pages: int = ROOSTER_MAX_PAGES,
                 transport: httpx.BaseTransport | None = None):
        self.url = url
        self.extra = extra if extra is not None else {
            "query": list(ROOSTER_QUERY),
            "filters": self._load_filters(ROOSTER_FILTERS),
        }
        self.limit = limit
        self.max_pages = max_pages
        self.transport = transport  # lets tests inject a fake server

    @staticmethod
    def _load_filters(raw: str) -> dict:
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"ROOSTER_FILTERS is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("ROOSTER_FILTERS must be a JSON object")
        return data

    def fetch(self) -> list[RawJob]:
        if not self.url:
            raise RuntimeError("ROOSTER_API_URL is not set")

        jobs: list[RawJob] = []
        with httpx.Client(headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                          timeout=REQUEST_TIMEOUT, transport=self.transport) as client:
            for page in range(1, self.max_pages + 1):
                resp = client.post(self.url, json={**self.extra, "page": page, "limit": self.limit})
                resp.raise_for_status()
                batch = self.parse(resp.json())
                jobs.extend(batch)
                if len(batch) < self.limit:
                    break  # last page
                if page < self.max_pages:
                    time.sleep(REQUEST_DELAY_SECONDS)
        return jobs

    @staticmethod
    def parse(payload: dict) -> list[RawJob]:
        body = payload.get("body")
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise ValueError("Unexpected Rooster response shape (no body.data list)")

        jobs: list[RawJob] = []
        for item in body["data"]:
            job_id, title = item.get("id"), (item.get("title") or "").strip()
            if not job_id or not title:
                continue

            posted = None
            if item.get("created_at"):
                try:
                    posted = datetime.fromisoformat(item["created_at"])
                except ValueError:
                    pass

            description = item.get("description") or ""
            salary = RoosterCollector._salary(item)
            if salary:
                description = f"Salary: {salary}\n\n{description}"

            jobs.append(RawJob(
                title=title,
                url=JOB_URL.format(id=job_id),
                company=item.get("subsidiary_company_name") or item.get("company_name") or "",
                location=item.get("location") or "",
                description=description,
                remote=bool(item.get("remote")),
                posted_at=posted,
            ))
        return jobs

    @staticmethod
    def _salary(item: dict) -> str:
        lo, hi = item.get("min_salary"), item.get("max_salary")
        if not lo and not hi:
            return ""
        cur = item.get("salary_currency") or ""
        per = f"/{item['salary_frequency']}" if item.get("salary_frequency") else ""
        amount = f"{lo:,}" if lo == hi or not hi else f"{lo:,} - {hi:,}"
        return f"{cur} {amount}{per}".strip()
