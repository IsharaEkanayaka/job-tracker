import pytest
from backend.processing.filter import score_job


@pytest.mark.parametrize("title", [
    "Senior Python Developer", "Embedded Firmware Engineer",
    "Full-Stack Engineer", "Backend Developer (Node.js)",
])
def test_software_titles_pass(title):
    assert score_job(title, "")[0] is True


@pytest.mark.parametrize("title", [
    "Sales Manager", "Civil Engineer", "Marketing Executive", "Customer Support Agent",
])
def test_non_software_titles_fail(title):
    assert score_job(title, "")[0] is False


def test_sales_engineer_is_excluded():
    assert score_job("Sales Engineer", "Python SQL API")[0] is False


def test_description_can_rescue_vague_title():
    desc = "You will build REST APIs with Python, Docker, AWS, Git and Postgres."
    assert score_job("Technical Specialist", desc)[0] is True


@pytest.mark.parametrize("title", [
    "QA Engineer", "Senior QA Engineer", "Quality Assurance Analyst", "SDET",
    "Software Test Engineer", "Test Automation Engineer", "Software Engineer in Test",
    "Quality Engineer", "QA Automation Tester",
])
def test_qa_and_testing_roles_are_rejected(title):
    # even a description full of tech keywords must not rescue them
    desc = "Python, Selenium, SQL, API testing, Git, Docker, CI/CD, AWS"
    assert score_job(title, desc)[0] is False


@pytest.mark.parametrize("title", [
    "Backend Developer (Qatar)", "Salesforce Developer", "Python Developer - Aqaba",
])
def test_whole_word_matching_avoids_false_rejections(title):
    assert score_job(title, "Python SQL Git Docker API")[0] is True


def test_extra_exclusions_from_config(monkeypatch):
    assert score_job("Intern - Python Developer", "Python SQL Git Docker API")[0] is True
    monkeypatch.setattr("backend.processing.filter.EXCLUDE_KEYWORDS", ["intern"])
    assert score_job("Intern - Python Developer", "Python SQL Git Docker API")[0] is False
