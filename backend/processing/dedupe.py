import hashlib
import re


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def dedupe_hash(title: str, company: str, location: str = "") -> str:
    """Same job posted on several sources -> same hash."""
    key = f"{_norm(title)}|{_norm(company)}|{_norm(location)}"
    return hashlib.sha256(key.encode()).hexdigest()
