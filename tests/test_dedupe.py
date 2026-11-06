from backend.processing.dedupe import dedupe_hash


def test_same_job_same_hash():
    assert dedupe_hash("Backend Dev", "Acme Inc.", "Remote") == \
           dedupe_hash("  backend   dev ", "ACME Inc", "remote")


def test_different_company_different_hash():
    assert dedupe_hash("Backend Dev", "Acme") != dedupe_hash("Backend Dev", "Globex")
