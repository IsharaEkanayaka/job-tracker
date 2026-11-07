"""App settings. Every value can be overridden with an environment variable or a
`.env` file in the project root (copy .env.example to .env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env if present; real environment variables still win


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


# --- general ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # the folder that contains backend/ and frontend/
# The default database file always lives in the project root, whichever folder you start the server from.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'jobs.db').as_posix()}")
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "5"))
# Extra title words to reject, comma-separated, e.g. "intern,support". Added to the built-in list.
EXCLUDE_KEYWORDS = _list("EXCLUDE_KEYWORDS", "")
REQUEST_TIMEOUT = 20
REQUEST_DELAY_SECONDS = 1.5  # pause between paged requests
USER_AGENT = "job-tracker/0.1 (personal project)"

# --- ITPro.lk ---
ITPRO_CATEGORY_URL = os.getenv(
    "ITPRO_CATEGORY_URL", "https://itpro.lk/jobs/software-engineering/"
)
ITPRO_MAX_PAGES = int(os.getenv("ITPRO_MAX_PAGES", "30"))

# --- Rooster.jobs (the JSON search endpoint the website itself uses) ---
# Set ROOSTER_API_URL= (empty) in .env to disable this collector.
ROOSTER_API_URL = os.getenv("ROOSTER_API_URL", "https://api.rooster.jobs/jobSearch/jobs/search")
# Search terms are combined with OR. Comma-separated.
ROOSTER_QUERY = _list(
    "ROOSTER_QUERY",
    "software engineer,developer,backend,frontend,full stack,embedded,firmware,devops,ai,engineer,ml,python,java,javascript,node,react,angular,vue,django,flask,ruby,rust,c++,c#,golang,php",
)
ROOSTER_COUNTRY = os.getenv("ROOSTER_COUNTRY", "Sri Lanka")
ROOSTER_FILTERS = os.getenv(
    "ROOSTER_FILTERS", f'{{"country": "{ROOSTER_COUNTRY}"}}'
)  # JSON object
