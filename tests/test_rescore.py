from sqlalchemy import select

from backend.db.models import Job
from backend.rescore import rescore


def _job(db, title, flag):
    db.add(Job(title=title, source="t", description="Python SQL Git Docker API",
               is_software=flag, score=9, dedupe_hash=title))


def test_rescore_preview_then_apply(db):
    _job(db, "QA Engineer", True)          # saved before QA was excluded
    _job(db, "Backend Developer", True)    # stays
    _job(db, "Python Developer", False)    # was wrongly hidden
    db.commit()

    preview = rescore(db, apply=False)
    assert preview["now_hidden"] == ["QA Engineer"]
    assert preview["now_shown"] == ["Python Developer"]
    assert db.scalar(select(Job.is_software).where(Job.title == "QA Engineer")) is True  # untouched

    rescore(db, apply=True)
    flags = {j.title: j.is_software for j in db.scalars(select(Job)).all()}
    assert flags == {"QA Engineer": False, "Backend Developer": True, "Python Developer": True}
    assert db.scalar(select(Job).where(Job.title == "QA Engineer")) is not None  # nothing deleted
