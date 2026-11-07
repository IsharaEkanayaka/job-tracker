# Job Tracker

Collects software job posts from multiple sources, filters out non-software roles,
removes duplicates, and tracks your applications.

## Architecture

```
Collectors -> Normalizer -> Software filter -> Deduplicator -> DB -> FastAPI -> UI
(one class per source)                                          ^
Scheduler (APScheduler) triggers collectors                     |
Manual input (WhatsApp / LinkedIn pastes) -> POST /jobs/manual -+
```

- **Collectors** share one interface (`BaseCollector.fetch() -> list[RawJob]`). A new source is one new file.
- **Filter** is rule-based scoring (title match, tech keywords in description, exclude words).
- **Dedupe** hashes normalized `title + company + location`.
- **Pipeline** is idempotent, and one failing source never breaks the others (errors go to `scrape_runs`).

## Project layout

```
job-tracker/              <- project root: run every command from here
├── backend/              Python package (FastAPI, collectors, processing, db)
├── frontend/             React app (Vite)
├── tests/
├── requirements.txt, pytest.ini, .env, .gitignore
└── jobs.db               created on first run (git-ignored)
```

## Run

Backend (terminal 1):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn backend.api.main:app --reload    # API docs at http://127.0.0.1:8000/docs
```

Frontend, development (terminal 2). Hot reload, proxies API calls to FastAPI:

```bash
cd frontend
npm install
npm run dev                          # open http://localhost:5173
```

Frontend, production. FastAPI serves the built app itself:

```bash
cd frontend && npm run build         # then open http://127.0.0.1:8000
```

Other commands: `python -m backend.scheduler` (background worker: collect at startup and every
6 hours), `pytest` (backend tests). The worker stores all jobs it can collect, including their
published dates. The UI date selector queries these saved jobs and does not trigger a new fetch.

## Frontend

React 18 + Vite, no UI library. `src/api.js` holds all API calls, `src/components/` has
`PipelineStrip`, `Filters`, `JobList`, `JobRow` and `AddJobDialog`, and `App.jsx` owns the state.
Stale requests are cancelled with `AbortController` when filters change quickly.

## Configuration

Defaults live in `backend/config.py`. To change them, copy `.env.example` to `.env`
(`Copy-Item .env.example .env` in PowerShell) and edit it. The `.env` file is git-ignored.

| Variable | Default | Meaning |
|---|---|---|
| `ROOSTER_API_URL` | Rooster search endpoint | Empty value turns the collector off |
| `ROOSTER_QUERY` | `software engineer,developer,...` | Search terms, combined with OR |
| `ROOSTER_FILTERS` | `{}` | JSON filters sent to the endpoint |
| `ROOSTER_LIMIT` | `20` | Jobs per request |
| `ROOSTER_MAX_PAGES` | `5` | Requests per fetch (raise to 30 once for a full backfill) |
| `DATABASE_URL` | `jobs.db` in the project root | Database |
| `ITPRO_CATEGORY_URL` | ITPro software engineering category | Empty value turns the collector off |
| `ITPRO_MAX_PAGES` | `30` | Maximum ITPro category pages per fetch |

## Filtering

`backend/processing/filter.py` scores each job title and description. QA and testing roles are
rejected, and you can add more rejected title words with `EXCLUDE_KEYWORDS` in `.env`.
After changing the rules, re-check jobs you already saved:

```bash
python -m backend.rescore            # preview what would change
python -m backend.rescore --apply    # save the changes (nothing is deleted)
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/jobs?q=&source=&software_only=&remote=` | List/filter jobs |
| POST | `/jobs/manual` | Add a job from WhatsApp/LinkedIn |
| PUT | `/jobs/{id}/application` | Set status: saved/applied/interview/rejected/offer |
| GET | `/stats` | Jobs per source, applications per status |
| POST | `/collect/run` | Run all collectors now |
| GET | `/jobs?posted_from=YYYY-MM-DD&posted_to=YYYY-MM-DD` | Filter saved jobs by published date |

The UI date selector supports all dates, the last 1, 2, or 7 days, the last 2 weeks,
the last month, and a custom inclusive date range. It filters saved jobs and does not
delete them. Use the **Fetch new jobs** button for an immediate worker run; normally
`python -m backend.scheduler` keeps ingestion running every 6 hours.

## Roadmap

- [ ] Rooster.jobs collector (`backend/collectors/rooster.py`)
- [x] ITPro.lk software engineering collector (`backend/collectors/itpro_lk.py`)
- [ ] More remote sources (RemoteOK, We Work Remotely, HN "Who is hiring")
- [ ] Telegram bot to forward WhatsApp posts + LLM parser for messy text
- [x] Web UI (React): stage pipeline, filters, notes, add-job form
- [ ] Daily digest notifications
- [ ] Docker + deployment
- [ ] Measure filter accuracy on a hand-labeled set of 200 jobs
