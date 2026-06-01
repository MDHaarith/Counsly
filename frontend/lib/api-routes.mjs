export const API_ENDPOINTS = Object.freeze({
  auth: Object.freeze({
    session: "/auth/session",
    verifyRoll: "/auth/verify-roll",
  }),
  choices: Object.freeze({
    collection: "/choices/",
    reorder: "/choices/reorder",
    snapshots: "/choices/snapshots",
    upload: "/choices/upload",
  }),
  compare: Object.freeze({
    collection: "/compare/",
    sessions: "/compare/sessions",
  }),
  explore: Object.freeze({
    base: "/explore",
    search: "/explore/search",
  }),
  guidance: Object.freeze({
    onboarding: "/guidance/onboarding",
  }),
  logging: Object.freeze({
    clientError: "/logging/client-error",
  }),
  maps: Object.freeze({
    colleges: "/maps/colleges",
    tfcLocations: "/maps/tfc-locations",
  }),

  workspace: Object.freeze({
    settings: "/workspace/settings",
  }),
});

export function withQuery(path, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    query.set(key, String(value));
  });
  const suffix = query.toString();
  return suffix ? `${path}?${suffix}` : path;
}

export function choiceDetailPath(choiceId) {
  // Composed from API_ENDPOINTS.choices.collection which is "/choices/"
  return `${API_ENDPOINTS.choices.collection}${encodeURIComponent(choiceId)}`;
}

export function exploreDetailPath(collegeCode, community = "") {
  // Composed from API_ENDPOINTS.explore.base which is "/explore"
  return withQuery(`${API_ENDPOINTS.explore.base}/${encodeURIComponent(collegeCode)}`, { community });
}

export function choiceSnapshotRestorePath(snapshotId) {
  // Composed from API_ENDPOINTS.choices.snapshots which is "/choices/snapshots"
  return `${API_ENDPOINTS.choices.snapshots}/${encodeURIComponent(snapshotId)}/restore`;
}
