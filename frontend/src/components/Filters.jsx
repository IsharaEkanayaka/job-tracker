import { formatDate } from "../utils";

export default function Filters({
  q, onQ, source, onSource, sources,
  remote, onRemote, showAll, onShowAll, canShowAll,
  skipped, skippedCount, onToggleSkipped,
  datePreset, onDatePreset, dateStart, onDateStart, dateEnd, onDateEnd,
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
      <label className="date-range">
        Published:
        <select value={datePreset} onChange={(e) => {
          const value = e.target.value;
          onDatePreset(value);
          if (value !== "custom") {
            const end = new Date();
            const start = new Date(end);
            if (value === "month") start.setMonth(start.getMonth() - 1);
            else if (value !== "all") start.setDate(start.getDate() - (Number(value) - 1));
            onDateStart(value === "all" ? "" : formatDate(start));
            onDateEnd(value === "all" ? "" : formatDate(end));
          }
        }} aria-label="Published date range">
          <option value="all">All dates</option>
          <option value="1">Last 1 day</option>
          <option value="2">Last 2 days</option>
          <option value="7">Last 7 days</option>
          <option value="14">Last 2 weeks</option>
          <option value="month">Last 1 month</option>
          <option value="custom">Custom range</option>
        </select>
      </label>
      {datePreset === "custom" && (
        <div className="custom-dates">
          <label>From <input type="date" value={dateStart} onChange={(e) => onDateStart(e.target.value)} /></label>
          <label>To <input type="date" value={dateEnd} onChange={(e) => onDateEnd(e.target.value)} /></label>
        </div>
      )}
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
