// The main pipeline, shown as the strip at the top.
export const FUNNEL = [
  { key: "none", label: "New" },
  { key: "saved", label: "Saved" },
  { key: "applied", label: "Applied" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "rejected", label: "Rejected" },
];

// Parked jobs you don't want to focus on right now. Kept out of the pipeline strip on purpose.
export const SKIPPED = { key: "skipped", label: "Skipped" };

export const STAGES = [...FUNNEL, SKIPPED];
export const TRACKED_STAGES = STAGES.filter((s) => s.key !== "none");
export const PAGE_SIZE = 30;
