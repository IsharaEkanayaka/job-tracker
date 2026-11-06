import { FUNNEL } from "../constants";

export default function PipelineStrip({ stats, stage, onSelect }) {
  const counts = { none: stats?.new_jobs ?? 0, ...(stats?.applications_per_status ?? {}) };

  return (
    <nav className="pipeline" aria-label="Application stages">
      {FUNNEL.map((s) => (
        <button
          key={s.key}
          type="button"
          className="stage"
          aria-pressed={stage === s.key}
          style={{ "--c": `var(--c-${s.key})` }}
          onClick={() => onSelect(s.key)}
        >
          <span className="n">{counts[s.key] ?? 0}</span>
          <span className="l">{s.label}</span>
        </button>
      ))}
    </nav>
  );
}
