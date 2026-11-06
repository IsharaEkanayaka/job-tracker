export default function Filters({
  q, onQ, source, onSource, sources,
  remote, onRemote, showAll, onShowAll, canShowAll,
  skipped, skippedCount, onToggleSkipped,
}) {
  return (
    <div className="filters">
      <input
        type="search"
        value={q}
        onChange={(e) => onQ(e.target.value)}
        placeholder="Search title or company"
        aria-label="Search title or company"
      />
      <select value={source} onChange={(e) => onSource(e.target.value)} aria-label="Source">
        <option value="">All sources</option>
        {sources.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <label className="check">
        <input type="checkbox" checked={remote} onChange={(e) => onRemote(e.target.checked)} />
        Remote only
      </label>
      {canShowAll && (
        <label className="check">
          <input type="checkbox" checked={showAll} onChange={(e) => onShowAll(e.target.checked)} />
          Include non-software
        </label>
      )}
      <button type="button" className="skipped-toggle" aria-pressed={skipped} onClick={onToggleSkipped}>
        Skipped <span className="count">{skippedCount}</span>
      </button>
    </div>
  );
}
