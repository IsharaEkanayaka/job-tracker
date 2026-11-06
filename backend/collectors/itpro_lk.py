import time
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from backend.collectors.base import BaseCollector, RawJob
from backend.config import (
    ITPRO_CATEGORY_URL,
    ITPRO_MAX_PAGES,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

BASE_URL = "https://itpro.lk"


class ItProCollector(BaseCollector):
    """Collect software engineering jobs from ITPro.lk's category pages."""

    name = "itpro"

    def __init__(
        self,
        category_url: str = ITPRO_CATEGORY_URL,
        max_pages: int = ITPRO_MAX_PAGES,
        transport: httpx.BaseTransport | None = None,
    ):
        self.category_url = category_url
        self.max_pages = max_pages
        self.transport = transport

    def fetch(self) -> list[RawJob]:
        if not self.category_url:
            raise RuntimeError("ITPRO_CATEGORY_URL is not set")
        if self.max_pages < 1:
            raise ValueError("ITPRO_MAX_PAGES must be at least 1")

        jobs: list[RawJob] = []
        seen_ids: set[str] = set()
        first_page_id: str | None = None

        with httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            transport=self.transport,
        ) as client:
            for page in range(1, self.max_pages + 1):
                url = self.category_url if page == 1 else f"{self.category_url}?p={page}&"
                response = client.get(url)
                response.raise_for_status()
                cards = self.parse_cards(response.text)

                if not cards:
                    break
                if page > 1 and cards[0].get("id") == first_page_id:
                    break
                if page == 1:
                    first_page_id = cards[0].get("id")

                for card in cards:
                    job_id = card.get("id")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    jobs.append(self._to_raw_job(card))

                if page < self.max_pages:
                    time.sleep(REQUEST_DELAY_SECONDS)

        return jobs

    @staticmethod
    def parse_cards(html: str) -> list[dict[str, str | None]]:
        soup = BeautifulSoup(html, "html.parser")
        cards: list[dict[str, str | None]] = []
        for card in soup.select("article.job-card"):
            link = card.select_one("a.jcl")
            title = card.select_one(".jc-title")
            company = card.select_one(".jc-company")
            cards.append(
                {
                    "id": card.get("id"),
                    "title": title.get_text(strip=True) if title else None,
                    "company": company.get_text(strip=True) if company else None,
                    "url": urljoin(
                        BASE_URL, link.get("href", "")
                    ) if link else None,
                }
            )
        return cards

    @staticmethod
    def _to_raw_job(card: dict[str, str | None]) -> RawJob:
        return RawJob(
            title=card.get("title") or "",
            company=card.get("company") or "",
            url=card.get("url") or "",
        )