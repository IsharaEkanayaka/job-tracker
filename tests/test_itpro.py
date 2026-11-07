import httpx

from backend.collectors.itpro_lk import ItProCollector


PAGE_ONE = """
<article class="job-card" id="job-1">
  <a class="jcl" href="/jobs/python-developer/">View</a>
  <h2 class="jc-title"> Python Developer </h2>
  <span class="jc-company">Acme Ltd</span>
  <span class="jc-company-info"><span class="la">Colombo</span></span>
  <time class="time-posted" datetime="2026-11-07T10:00:00+05:30">Today</time>
</article>
<article class="job-card" id="job-2">
  <a class="jcl" href="https://itpro.lk/jobs/frontend-engineer/">View</a>
  <h2 class="jc-title">Frontend Engineer</h2>
  <span class="jc-company">Globex</span>
</article>
"""

PAGE_TWO = """
<article class="job-card" id="job-3">
  <a class="jcl" href="/jobs/backend-engineer/">View</a>
  <h2 class="jc-title">Backend Engineer</h2>
  <span class="jc-company">Initech</span>
</article>
"""


def test_fetch_maps_cards_and_stops_at_empty_page(monkeypatch):
    monkeypatch.setattr("backend.collectors.itpro_lk.time.sleep", lambda _: None)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("p") == "2":
            return httpx.Response(200, text=PAGE_TWO)
        return httpx.Response(200, text=PAGE_ONE)

    collector = ItProCollector(
        category_url="https://itpro.lk/jobs/software-engineering/",
        max_pages=3,
        transport=httpx.MockTransport(handler),
    )

    jobs = collector.fetch()

    assert [job.title for job in jobs] == [
        "Python Developer",
        "Frontend Engineer",
        "Backend Engineer",
    ]
    assert jobs[0].company == "Acme Ltd"
    assert jobs[0].location == "Colombo"
    assert jobs[0].posted_at is not None
    assert jobs[0].url == "https://itpro.lk/jobs/python-developer/"


def test_fetch_stops_when_itpro_returns_page_one_again(monkeypatch):
    monkeypatch.setattr("backend.collectors.itpro_lk.time.sleep", lambda _: None)
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, text=PAGE_ONE)

    collector = ItProCollector(
        category_url="https://itpro.lk/jobs/software-engineering/",
        max_pages=5,
        transport=httpx.MockTransport(handler),
    )

    assert len(collector.fetch()) == 2
    assert requests == [
        "https://itpro.lk/jobs/software-engineering/",
        "https://itpro.lk/jobs/software-engineering/?p=2&",
    ]


def test_fetch_rejects_empty_category_url():
    collector = ItProCollector(category_url="")

    try:
        collector.fetch()
    except RuntimeError as exc:
        assert str(exc) == "ITPRO_CATEGORY_URL is not set"
    else:
        raise AssertionError("Expected an unset category URL to fail")
