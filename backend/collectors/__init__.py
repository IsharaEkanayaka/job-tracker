from backend.collectors.base import BaseCollector, RawJob
from backend.collectors.itpro_lk import ItProCollector
from backend.collectors.remotive import RemotiveCollector
from backend.collectors.rooster import RoosterCollector
from backend.config import ITPRO_CATEGORY_URL, ROOSTER_API_URL

# Register new collectors here.
ALL_COLLECTORS: list[type[BaseCollector]] = [RemotiveCollector]
if ITPRO_CATEGORY_URL:
    ALL_COLLECTORS.append(ItProCollector)
if ROOSTER_API_URL:  # only active once you've configured the endpoint
    ALL_COLLECTORS.append(RoosterCollector)

__all__ = [
    "BaseCollector",
    "RawJob",
    "ItProCollector",
    "RemotiveCollector",
    "RoosterCollector",
    "ALL_COLLECTORS",
]
