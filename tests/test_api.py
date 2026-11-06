def test_manual_job_and_application_flow(client):
    r = client.post("/jobs/manual", json={
        "title": "Junior Python Developer", "company": "Acme",
        "description": "Python, SQL, Git", "source": "whatsapp"})
    assert r.status_code == 201
    job_id = r.json()["id"]

    # duplicate rejected
    assert client.post("/jobs/manual", json={
        "title": "Junior Python Developer", "company": "Acme"}).status_code == 409

    r = client.put(f"/jobs/{job_id}/application", json={"status": "applied", "notes": "sent CV"})
    assert r.status_code == 200
    assert r.json()["application"]["status"] == "applied"
    assert r.json()["application"]["applied_at"] is not None

    assert client.put(f"/jobs/{job_id}/application", json={"status": "nope"}).status_code == 422

    jobs = client.get("/jobs", params={"q": "python"}).json()
    assert len(jobs) == 1

    s = client.get("/stats").json()
    assert s["jobs_per_source"] == {"whatsapp": 1}
    assert s["applications_per_status"] == {"applied": 1}


def test_index_serves_ui(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Job Tracker" in r.text  # API hint page or built UI


def test_stage_filter_and_new_count(client):
    a = client.post("/jobs/manual", json={"title": "Python Developer", "company": "A",
                                          "description": "Python SQL Git Docker API"}).json()
    client.post("/jobs/manual", json={"title": "Backend Developer", "company": "B",
                                      "description": "Python SQL Git Docker API"})
    client.put(f"/jobs/{a['id']}/application", json={"status": "interview"})

    assert [j["id"] for j in client.get("/jobs", params={"status": "interview"}).json()] == [a["id"]]
    assert len(client.get("/jobs", params={"status": "none"}).json()) == 1
    assert len(client.get("/jobs", params={"status": "any"}).json()) == 1

    s = client.get("/stats").json()
    assert s["new_jobs"] == 1
    assert "manual" in s["sources"]


def test_jobs_are_sorted_newest_posted_first(db, client):
    from datetime import datetime
    from backend.collectors.base import RawJob
    from backend.pipeline import save_raw_job

    for title, posted in [("Python Developer A", datetime(2026, 1, 1)),
                          ("Python Developer B", datetime(2026, 6, 1)),
                          ("Python Developer C", datetime(2026, 3, 1))]:
        save_raw_job(db, RawJob(title=title, url="", company=title[-1], description="Python SQL Git Docker API",
                                posted_at=posted), "test")
    db.commit()
    titles = [j["title"] for j in client.get("/jobs").json()]
    assert titles == ["Python Developer B", "Python Developer C", "Python Developer A"]


def test_skip_and_restore_job(client):
    a = client.post("/jobs/manual", json={"title": "Python Developer", "company": "A",
                                          "description": "Python SQL Git Docker API"}).json()
    assert client.get("/stats").json()["new_jobs"] == 1

    # skipping removes it from New but keeps it
    r = client.put(f"/jobs/{a['id']}/application", json={"status": "skipped"})
    assert r.status_code == 200
    assert client.get("/stats").json()["new_jobs"] == 0
    assert client.get("/jobs", params={"status": "none"}).json() == []
    assert [j["id"] for j in client.get("/jobs", params={"status": "skipped"}).json()] == [a["id"]]
    assert client.get("/stats").json()["applications_per_status"] == {"skipped": 1}

    # restoring puts it back in New
    r = client.delete(f"/jobs/{a['id']}/application")
    assert r.status_code == 200 and r.json()["application"] is None
    assert client.get("/stats").json()["new_jobs"] == 1
    assert client.get("/jobs", params={"status": "skipped"}).json() == []

    # restoring a job that was never tracked is harmless; unknown job is a 404
    assert client.delete(f"/jobs/{a['id']}/application").status_code == 200
    assert client.delete("/jobs/9999/application").status_code == 404
