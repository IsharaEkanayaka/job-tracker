"""Re-run the software filter on every saved job, e.g. after changing the keyword lists.

    python -m backend.rescore          # preview: show what would change
    python -m backend.rescore --apply  # save the changes

Only the is_software flag and score change. Nothing is deleted, and jobs you already
track (saved, applied, ...) stay visible in their stages.
"""
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import Job
from backend.db.session import SessionLocal, init_db
from backend.processing.filter import score_job


def rescore(db: Session, apply: bool = False) -> dict:
    hidden, shown, other = [], [], 0
    for job in db.scalars(select(Job)).all():
        is_software, score = score_job(job.title, job.description)
        if is_software != job.is_software:
            (shown if is_software else hidden).append(job.title)
        if score != job.score:
            other += 1
        if apply:
            job.is_software, job.score = is_software, score
    if apply:
        db.commit()
    return {"now_hidden": hidden, "now_shown": shown, "score_changes": other}


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    init_db()
    with SessionLocal() as session:
        result = rescore(session, apply=apply)
    print(f"{'Applied' if apply else 'Preview'}: {len(result['now_hidden'])} jobs now filtered out, "
          f"{len(result['now_shown'])} now shown.")
    for title in result["now_hidden"][:15]:
        print("  hidden:", title)
    for title in result["now_shown"][:15]:
        print("  shown: ", title)
    if not apply and (result["now_hidden"] or result["now_shown"]):
        print("Run again with --apply to save.")
