from datetime import datetime

import httpx

from backend.collectors.base import BaseCollector, RawJob
from backend.config import REQUEST_TIMEOUT, USER_AGENT

API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveCollector(BaseCollector):
    """Remotive public API. Docs: https://github.com/remotive-com/remote-jobs-api"""

    name = "remotive"

    def __init__(self, category: str = "software-dev", limit: int = 100):
        self.category = category
        self.limit = limit

    def fetch(self) -> list[RawJob]:
        resp = httpx.get(
            API_URL,
            params={"category": self.category, "limit": self.limit},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return self.parse(resp.json())

    @staticmethod
    def parse(payload: dict) -> list[RawJob]:
        jobs = []
        for item in payload.get("jobs", []):
            posted = None
            if item.get("publication_date"):
                try:
                    posted = datetime.fromisoformat(item["publication_date"])
                except ValueError:
                    pass
            jobs.append(
                RawJob(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    company=item.get("company_name", ""),
                    location=item.get("candidate_required_location", "") or "Remote",
                    description=item.get("description", ""),
                    remote=True,
                    posted_at=posted,
                )
            )
        return jobs
