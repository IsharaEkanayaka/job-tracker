import { PAGE_SIZE } from "./constants";

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(message);
  }
  return res.json();
}

export const getStats = (signal) => request("/stats", { signal });

export function getJobs(
  { stage, q, source, remote, showAll, dateStart, dateEnd },
  offset,
  signal,
) {
  const tracked = stage !== "none";
  const params = new URLSearchParams({
    limit: PAGE_SIZE,
    offset,
    status: stage,
    software_only: String(!(tracked || showAll)),
  });
  if (q) params.set("q", q);
  if (source) params.set("source", source);
  if (remote) params.set("remote", "true");
  if (dateStart) params.set("posted_from", dateStart);
  if (dateEnd) params.set("posted_to", dateEnd);
  return request(`/jobs?${params}`, { signal });
}

export const clearApplication = (jobId) =>
  request(`/jobs/${jobId}/application`, { method: "DELETE" });

export const runCollectors = () => request("/collect/run", { method: "POST" });

export const addManualJob = (job) =>
  request("/jobs/manual", { method: "POST", body: JSON.stringify(job) });

export const setApplication = (jobId, status, notes) =>
  request(`/jobs/${jobId}/application`, {
    method: "PUT",
    body: JSON.stringify({ status, notes }),
  });
