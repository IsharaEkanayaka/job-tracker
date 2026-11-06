"""Rule-based 'is this a software job I want?' scoring.

Scoring: +5 title include match, +1 per distinct tech keyword in the description
(capped), -10 for any exclude word in the title. An exclude word effectively vetoes
a job, because the description can add at most +5.

Words are matched as whole words, so "qa" does not match "Qatar" and "sales" does not
match "Salesforce". Add your own exclusions without touching code via EXCLUDE_KEYWORDS
in .env (comma-separated).
"""
import re

from backend.config import EXCLUDE_KEYWORDS, SCORE_THRESHOLD

TITLE_INCLUDE = [
    "software", "developer", "backend", "back-end", "frontend", "front-end",
    "full stack", "full-stack", "fullstack", "embedded", "firmware", "devops",
    "sre", "data engineer", "programmer",
    "python", "java", "react", "node", "golang", "rust", "c++",
]

TITLE_EXCLUDE = [
    # not software
    "sales", "marketing", "accountant", "recruiter", "civil engineer",
    "mechanical", "electrical engineer", "driver", "teacher", "nurse",
    "customer support", "customer success", "hr", "human resources",
    # QA / testing roles (not wanted)
    "qa", "quality assurance", "quality engineer", "sdet", "tester",
    "test engineer", "testing engineer", "test automation",
    "software engineer in test", "automation tester",
]

TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "sql", "api", "git", "docker",
    "kubernetes", "aws", "react", "node", "c++", "rust", "golang", "linux",
    "rest", "microservices", "ci/cd", "postgres", "firmware", "rtos",
]

DESCRIPTION_CAP = 5


def _has(text: str, word: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", text) is not None


def score_job(title: str, description: str = "") -> tuple[bool, int]:
    t = (title or "").lower()
    d = (description or "").lower()
    excludes = TITLE_EXCLUDE + [k.lower() for k in EXCLUDE_KEYWORDS]

    score = 0
    if any(_has(t, w) for w in TITLE_INCLUDE):
        score += 5
    if any(_has(t, w) for w in excludes):
        score -= 10
    score += min(sum(1 for k in TECH_KEYWORDS if _has(d, k)), DESCRIPTION_CAP)

    return score >= SCORE_THRESHOLD, score
