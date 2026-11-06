import { STAGES } from "../constants";
import JobRow from "./JobRow";

function EmptyState({ stage, filtered, onFetch }) {
  if (stage === "none" && !filtered) {
    return (
      <li className="empty">
        <strong>No new jobs yet</strong>
        <span>Fetch jobs from your sources, or add one you found on WhatsApp or LinkedIn.</span>
        <div>
          <button type="button" className="btn primary" onClick={onFetch}>Fetch new jobs</button>
        </div>
      </li>
    );
  }
  if (stage === "skipped") {
    return (
      <li className="empty">
        <strong>Nothing skipped</strong>
        <span>Use Skip on a job you don't want to focus on right now. It waits here until you restore it.</span>
      </li>
    );
  }
  const label = STAGES.find((s) => s.key === stage).label;
  return (
    <li className="empty">
      <strong>Nothing here</strong>
      <span>
        {stage === "none"
          ? "No jobs match these filters."
          : `No jobs in ${label} yet. Use the stage menu on a job to move it here.`}
      </span>
    </li>
  );
}

export default function JobList({ jobs, loading, stage, filtered, onFetch, onChanged, onMessage }) {
  return (
    <ul className="list">
      {jobs.map((job) => (
        <JobRow key={job.id} job={job} onChanged={onChanged} onMessage={onMessage} />
      ))}
      {!jobs.length && loading && <li className="empty"><span>Loading jobs…</span></li>}
      {!jobs.length && !loading && <EmptyState stage={stage} filtered={filtered} onFetch={onFetch} />}
    </ul>
  );
}
