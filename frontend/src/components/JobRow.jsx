import { useState } from "react";
import { TRACKED_STAGES } from "../constants";
import { clearApplication, setApplication } from "../api";
import { ago, safeUrl } from "../utils";

export default function JobRow({ job, onChanged, onMessage }) {
  const [open, setOpen] = useState(false);
  const [notes, setNotes] = useState(job.application?.notes ?? "");
  const stage = job.application?.status ?? "";
  const href = safeUrl(job.url);
  const showRemote = job.remote && !/remote/i.test(job.location);

  async function save(status, text, doneMessage) {
    try {
      await setApplication(job.id, status, text);
      onMessage(doneMessage);
      onChanged();
    } catch (err) {
      onMessage(`Could not save: ${err.message}`, true);
    }
  }

  async function skip() {
    await save("skipped", notes, "Skipped. You'll find it under Skipped.");
  }

  async function restore() {
    if (notes.trim() && !window.confirm("Moving this job back to New removes its notes. Continue?")) return;
    try {
      await clearApplication(job.id);
      setNotes("");
      onMessage("Moved back to New.");
      onChanged();
    } catch (err) {
      onMessage(`Could not restore: ${err.message}`, true);
    }
  }

  return (
    <li className="job">
      <div className="row">
        <div>
          {href ? (
            <a className="title" href={href} target="_blank" rel="noopener noreferrer">
              {job.title}
            </a>
          ) : (
            <span className="title">{job.title}</span>
          )}
          <div className="meta">
            {job.company && <span>{job.company}</span>}
            {job.location && <span>{job.location}</span>}
            {showRemote && <span>Remote</span>}
            {!job.is_software && (
              <span className="tag-off" title={`Match score ${job.score}`}>Filtered out</span>
            )}
          </div>
        </div>

        <span className="src">{job.source}</span>
        <span className="when">{ago(job.posted_at || job.fetched_at)}</span>

        <select
          className="stage-select"
          data-s={stage}
          value={stage}
          aria-label={`Stage for ${job.title}`}
          onChange={(e) =>
            e.target.value === "__new" ? restore() : save(e.target.value, notes, `Moved to ${e.target.value}.`)
          }
        >
          <option value="" disabled>Set stage…</option>
          {TRACKED_STAGES.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
          {stage && <option value="__new">Back to New</option>}
        </select>

        <div className="act">
          {!stage && (
            <button type="button" className="link-btn" onClick={skip} title="Move out of New without tracking it">
              Skip
            </button>
          )}
          {stage === "skipped" && (
            <button type="button" className="link-btn" onClick={restore}>Restore</button>
          )}
        </div>

        <button
          type="button"
          className="more"
          aria-expanded={open}
          aria-label={open ? "Hide details" : "Show details"}
          onClick={() => setOpen((o) => !o)}
        >
          ⌄
        </button>
      </div>

      {open && (
        <div className="detail">
          <p className="desc">
            {job.description ? job.description.slice(0, 4000) : "No description saved for this job."}
          </p>
          <div className="notes-row">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              aria-label="Notes"
              placeholder="Notes: contact, interview date, follow-ups"
            />
            <button
              type="button"
              className="btn"
              onClick={() => save(stage || "saved", notes, "Notes saved.")}
            >
              Save notes
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
