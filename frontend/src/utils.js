// Job links come from scraped data, so only allow http(s) links (blocks javascript: URLs).
export function safeUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

// The API returns UTC timestamps without a "Z", so add it before parsing.
export function ago(iso) {
  if (!iso) return "";
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso);
  const date = new Date(hasZone ? iso : iso + "Z");
  const days = Math.floor((Date.now() - date.getTime()) / 86_400_000);
  if (days < 1) return "today";
  if (days < 31) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}
