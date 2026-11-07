import { useCallback, useEffect, useState } from "react";
import { getJobs, getStats, runCollectors } from "./api";
import { PAGE_SIZE } from "./constants";
import useDebounce from "./hooks/useDebounce";
import PipelineStrip from "./components/PipelineStrip";
import Filters from "./components/Filters";
import JobList from "./components/JobList";
import AddJobDialog from "./components/AddJobDialog";

export default function App() {
  const [stage, setStage] = useState("none");
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [remote, setRemote] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ text: "", error: false });
  const [fetching, setFetching] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [version, setVersion] = useState(0);
  const [datePreset, setDatePreset] = useState("all");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");

  const debouncedQ = useDebounce(q);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  const say = useCallback((text, error = false) => setMessage({ text, error }), []);
  const filters = { stage, q: debouncedQ, source, remote, showAll, dateStart, dateEnd };

  // Stage counts and source list: reload after any change.
  useEffect(() => {
    const ac = new AbortController();
    getStats(ac.signal)
      .then(setStats)
      .catch((e) => e.name !== "AbortError" && say(`Could not load stats: ${e.message}`, true));
    return () => ac.abort();
  }, [version, say]);

  // Job list: reload when a filter changes. Aborting stops stale responses from overwriting newer ones.
  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    getJobs(filters, 0, ac.signal)
      .then((data) => {
        setJobs(data);
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch((e) => e.name !== "AbortError" && say(`Could not load jobs: ${e.message}`, true))
      .finally(() => !ac.signal.aborted && setLoading(false));
    return () => ac.abort();
  }, [stage, debouncedQ, source, remote, showAll, dateStart, dateEnd, version, say]);

  async function showMore() {
    try {
      const data = await getJobs(filters, jobs.length);
      setJobs((prev) => [...prev, ...data]);
      setHasMore(data.length === PAGE_SIZE);
    } catch (e) {
      say(`Could not load more jobs: ${e.message}`, true);
    }
  }

  async function fetchJobs() {
    setFetching(true);
    say("Running collectors…");
    try {
      const runs = await runCollectors();
      const failed = runs.some((r) => r.status !== "ok");
      say(
        runs
          .map((r) => (r.status === "ok" ? `${r.source}: ${r.new} new of ${r.found}` : `${r.source}: failed`))
          .join(", "),
        failed
      );
      refresh();
    } catch (e) {
      say(`Could not fetch jobs: ${e.message}`, true);
    } finally {
      setFetching(false);
    }
  }

  function jobAdded() {
    setDialogOpen(false);
    say("Job added.");
    setStage("none");
    setShowAll(true); // a manual post may not pass the software filter, so make sure it shows
    refresh();
  }

  return (
    <div className="wrap">
      <header className="top">
        <h1>Job Tracker</h1>
        <div className="actions">
          <button type="button" className="btn" onClick={() => setDialogOpen(true)}>Add job</button>
          <button type="button" className="btn primary" onClick={fetchJobs} disabled={fetching}>
            Fetch new jobs
          </button>
        </div>
      </header>
      <p className={`status-line${message.error ? " error" : ""}`} role="status" aria-live="polite">
        {message.text}
      </p>

      <PipelineStrip stats={stats} stage={stage} onSelect={setStage} />

      <Filters
        q={q} onQ={setQ}
        source={source} onSource={setSource} sources={stats?.sources ?? []}
        remote={remote} onRemote={setRemote}
        showAll={showAll} onShowAll={setShowAll} canShowAll={stage === "none"}
        skipped={stage === "skipped"}
        skippedCount={stats?.applications_per_status?.skipped ?? 0}
        onToggleSkipped={() => setStage(stage === "skipped" ? "none" : "skipped")}
        datePreset={datePreset} onDatePreset={setDatePreset}
        dateStart={dateStart} onDateStart={setDateStart}
        dateEnd={dateEnd} onDateEnd={setDateEnd}
      />

      <JobList
        jobs={jobs}
        loading={loading}
        stage={stage}
        filtered={Boolean(debouncedQ || source || remote)}
        onFetch={fetchJobs}
        onChanged={refresh}
        onMessage={say}
      />

      {hasMore && (
        <div className="loadmore">
          <button type="button" className="btn" onClick={showMore}>Show more</button>
        </div>
      )}

      <AddJobDialog open={dialogOpen} onClose={() => setDialogOpen(false)} onSaved={jobAdded} />
    </div>
  );
}
