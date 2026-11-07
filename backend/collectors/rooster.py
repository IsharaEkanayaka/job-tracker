import json
import time
from datetime import datetime

import httpx

from backend.collectors.base import BaseCollector, RawJob
from backend.config import (
    REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT, ROOSTER_API_URL, ROOSTER_FILTERS,
    ROOSTER_QUERY, USER_AGENT,
)

JOB_URL = "https://rooster.jobs/jobs/{id}"
PAGE_SIZE = 20


class RoosterCollector(BaseCollector):
    """Rooster.jobs. POSTs to the JSON search endpoint the website itself uses.

    The body must contain integer `page` and `limit`; the search terms and filters
    come from ROOSTER_QUERY and ROOSTER_FILTERS (see config.py). This is not a documented public API,
    so it can change without notice: keep the schedule gentle and fail loudly if
    the response shape changes.
    """

    name = "rooster"

    def __init__(self, url: str = ROOSTER_API_URL, extra: dict | None = None,
                 retries: int = 3,
                 transport: httpx.BaseTransport | None = None):
        self.url = url
        self.extra = extra if extra is not None else {
            "query": list(ROOSTER_QUERY),
            "filters": self._load_filters(ROOSTER_FILTERS),
        }
        self.retries = retries
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
        if self.retries < 1:
            raise ValueError("retries must be at least 1")

        jobs_by_id: dict[object, RawJob] = {}
        with httpx.Client(headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                          timeout=REQUEST_TIMEOUT, transport=self.transport) as client:
            expected_count: int | None = None
            page = 1
            while True:
                payload = self._fetch_page(client, page)
                body = payload["body"]
                count = body.get("count")
                if not isinstance(count, int) or count < 0:
                    raise ValueError("Rooster response has no valid integer body.count")
                if expected_count is None:
                    expected_count = count
                elif count != expected_count:
                    raise ValueError(
                        f"Rooster total changed during download: "
                        f"{expected_count} -> {count}"
                    )

                page_data = body["data"]
                if not page_data:
                    if len(jobs_by_id) < expected_count:
                        raise RuntimeError(
                            f"Rooster download stopped early: received "
                            f"{len(jobs_by_id)} of {expected_count} jobs"
                        )
                    break
                previous_count = len(jobs_by_id)
                for item in page_data:
                    if not isinstance(item, dict) or "id" not in item:
                        raise ValueError(f"Invalid Rooster job record on page {page}")
                    jobs_by_id[item["id"]] = self._parse_item(item)
                if len(jobs_by_id) >= expected_count:
                    break
                if len(jobs_by_id) == previous_count:
                    raise RuntimeError(f"Rooster page {page} contained no new jobs")
                page += 1
                time.sleep(REQUEST_DELAY_SECONDS)

            if expected_count is not None and len(jobs_by_id) != expected_count:
                raise RuntimeError(
                    f"Rooster download incomplete: received {len(jobs_by_id)} "
                    f"of {expected_count} jobs"
                )
        return list(jobs_by_id.values())

    def _fetch_page(self, client: httpx.Client, page: int) -> dict:
        payload = {**self.extra, "page": page, "limit": PAGE_SIZE}
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = client.post(self.url, json=payload)
                response.raise_for_status()
                result = response.json()
                body = result.get("body") if isinstance(result, dict) else None
                if not isinstance(body, dict) or not isinstance(body.get("data"), list):
                    raise ValueError(
                        "Unexpected Rooster response shape "
                        "(no body.data list)"
                    )
                return result
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500 and exc.response.status_code not in {408, 429}:
                    raise
                last_error = exc
            except (httpx.RequestError, ValueError) as exc:
                last_error = exc
            if attempt + 1 < self.retries:
                time.sleep(2**attempt)
        raise RuntimeError(f"Unable to fetch Rooster page {page}: {last_error}") from last_error

    @staticmethod
    def _parse_item(item: dict) -> RawJob:
        jobs = RoosterCollector.parse({"body": {"data": [item]}})
        if not jobs:
            raise ValueError("Rooster job record has no title")
        return jobs[0]

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
