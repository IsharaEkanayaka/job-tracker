from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawJob:
    """Common shape every collector must return."""
    title: str
    url: str
    company: str = ""
    location: str = ""
    description: str = ""
    remote: bool = False
    posted_at: datetime | None = None


class BaseCollector(ABC):
    """Each job source implements this. Adding a source = adding one file."""

    name: str = "base"

    @abstractmethod
    def fetch(self) -> list[RawJob]:
        """Fetch jobs from the source and return them in the common format."""
