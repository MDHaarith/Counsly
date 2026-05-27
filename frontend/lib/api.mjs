import { logApiError, readStoredUser, shouldLogApiError } from "./error-logging.mjs";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");
export const SESSION_TOKEN_KEY = "counsly_access_token";

const fallbackBranch = {
  code: "CS",
  name: "Computer Science and Engineering",
};

function fitBandForScore(score) {
  if (score >= 92) return "Safe";
  if (score >= 84) return "Moderate";
  return "Ambitious";
}

export function cleanCollegeName(name) {
  if (!name) return name;
  if (name.includes("University Departments of Anna University, Chennai - ")) {
    const parts = name.split(" - ");
    const campus = parts[1].split(",")[0];
    return `Anna University - ${campus}`;
  }
  if (name.includes("University College of Engineering,")) {
    const parts = name.split(",");
    const city = parts[1].trim();
    return `University College of Engineering, ${city}`;
  }
  const parts = name.split(",");
  const first = parts[0].trim();
  const lower = first.toLowerCase();
  if (lower.includes("college") || lower.includes("institute") || lower.includes("university") || lower.includes("academy") || lower.includes("school")) {
    return first;
  }
  return name;
}

export function apiUrl(path) {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function readBrowserStorage(key) {
  if (typeof window === "undefined") return "";

  const sessionValue = window.sessionStorage?.getItem(key) || "";
  if (sessionValue) return sessionValue;

  const legacyValue = window.localStorage?.getItem(key) || "";
  if (legacyValue && window.sessionStorage) {
    window.sessionStorage.setItem(key, legacyValue);
    window.localStorage?.removeItem(key);
  }
  return legacyValue;
}

function writeBrowserStorage(key, value) {
  if (typeof window === "undefined" || !value) return;
  window.sessionStorage?.setItem(key, value);
  window.localStorage?.removeItem(key);
}

function clearBrowserStorage(key) {
  if (typeof window === "undefined") return;
  window.sessionStorage?.removeItem(key);
  window.localStorage?.removeItem(key);
}

export function getStoredToken() {
  return readBrowserStorage(SESSION_TOKEN_KEY);
}

export function saveStoredToken(token) {
  writeBrowserStorage(SESSION_TOKEN_KEY, token);
}

export function clearStoredToken() {
  clearBrowserStorage(SESSION_TOKEN_KEY);
}

export function buildRequestInit(options = {}, token = "") {
  const { body, headers = {}, ...rest } = options;
  const nextHeaders = { ...headers };
  let nextBody = body;

  if (token) nextHeaders.Authorization = `Bearer ${token}`;

  if (body && !(typeof FormData !== "undefined" && body instanceof FormData) && typeof body !== "string") {
    nextHeaders["Content-Type"] = nextHeaders["Content-Type"] || "application/json";
    nextBody = JSON.stringify(body);
  }

  return {
    ...rest,
    headers: nextHeaders,
    ...(nextBody === undefined ? {} : { body: nextBody }),
  };
}

async function parseFailure(response) {
  try {
    const payload = await response.json();
    return payload.detail || payload.message || `Backend request failed (${response.status}).`;
  } catch {
    return `Backend request failed (${response.status}).`;
  }
}

export async function apiRequest(path, options = {}) {
  const response = await fetch(apiUrl(path), buildRequestInit(options, getStoredToken()));
  if (!response.ok) {
    const message = await parseFailure(response);
    if (shouldLogApiError(response.status)) {
      const user = readStoredUser();
      await logApiError({
        endpoint: path,
        errorType: "server_error",
        message,
        status: response.status,
        userId: user?.id,
      }, { baseUrl: API_BASE_URL });
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

export function buildChoiceRow(choice) {
  const fitBand = choice.category || "Moderate";
  return {
    id: `choice-${choice.id}`,
    backendId: choice.id,
    code: choice.college_code,
    name: cleanCollegeName(choice.college_name),
    district: choice.district || "District pending",
    type: choice.type || "Self-Finance",
    branchCode: choice.branch_code,
    branchName: choice.branch_name,
    cutoff: choice.cutoff_mark_2025 || 0,
    cutoffRank: choice.cutoff_rank_2025 || 0,
    seats: choice.seats || 0,
    autonomous: Boolean(choice.is_autonomous),
    nba: Boolean(choice.nba_accredited),
    hostel: Boolean(choice.hostel_available),
    transport: Boolean(choice.transport_available),
    fees: choice.fee_structure_annual || 0,
    placementRate: choice.placement_rate_pct || 0,
    averagePackage: choice.avg_package_lpa || 0,
    railway: choice.nearest_railway_station || "Rail context pending",
    distanceKm: choice.nearest_railway_distance_km || 0,
    fitScore: choice.fit_score || 0,
    fitBand,
    priority: choice.priority,
    notes: choice.notes || "",
    manual: Boolean(choice.category),
  };
}

export function buildExploreCollege(college, branch = fallbackBranch) {
  return {
    code: college.code,
    name: cleanCollegeName(college.name),
    district: college.district,
    type: college.type,
    branchCode: branch.code,
    branchName: branch.name,
    cutoff: college.cutoff_mark_2025 || 0,
    cutoffRank: college.cutoff_rank_2025 || 0,
    seats: college.seats || 0,
    autonomous: Boolean(college.is_autonomous),
    nba: Boolean(college.nba_accredited),
    hostel: Boolean(college.hostel_available),
    transport: Boolean(college.transport_available),
    fees: college.fee_structure_annual || 0,
    placementRate: college.placement_rate_pct || 0,
    averagePackage: college.avg_package_lpa || 0,
    railway: college.nearest_railway_station || "Rail context pending",
    railwayLatitude: college.nearest_railway_station_latitude,
    railwayLongitude: college.nearest_railway_station_longitude,
    distanceKm: college.nearest_railway_distance_km || 0,
    fitScore: college.fit_score || 0,
    fitBand: fitBandForScore(college.fit_score || 0),
  };
}

export function buildCollegeDetail(detail) {
  const firstBranch = detail.branches?.[0] || fallbackBranch;
  const branch = {
    code: firstBranch.code || fallbackBranch.code,
    name: firstBranch.name || fallbackBranch.name,
  };

  return {
    ...buildExploreCollege(
      {
        ...detail,
        fit_score: detail.fit_score || 0,
        seats: firstBranch.approved_intake || firstBranch.seats?.total || 0,
      },
      branch,
    ),
    address: detail.address || "",
    latitude: detail.latitude,
    longitude: detail.longitude,
    website: detail.website || "",
    branches: detail.branches || [],
    cutoffTrends: detail.cutoff_trends || {},
    nearestTfc: detail.nearest_tfc || null,
    detailsRaw: detail.details_raw || null,
  };
}

export function buildCompareSession(session) {
  const ids = new URLSearchParams({
    ids: (session.college_codes || []).join(","),
    branches: (session.branch_codes || []).join(","),
  });
  return {
    id: `compare-${session.id}`,
    title: session.session_name || "Saved compare",
    collegeCodes: session.college_codes || [],
    branchCodes: session.branch_codes || [],
    createdAt: session.created_at || "",
    href: `/compare?${ids.toString()}`,
  };
}

export function buildWorkspaceSettings(settings = {}) {
  return {
    defaultDistrict: settings.default_district || "",
    preferredBranches: settings.preferred_branches || [],
    compactView: Boolean(settings.compact_view),
    mobileDensity: settings.mobile_density || "default",
    themeMode: settings.theme_mode || "mild",
  };
}

export async function startSession(payload) {
  const session = await apiRequest("/auth/session", { body: payload, method: "POST" });
  saveStoredToken(session.access_token);
  return session;
}

export async function fetchChoices() {
  const rows = await apiRequest("/choices/");
  return rows.map(buildChoiceRow);
}

export function reorderChoices(choices) {
  return apiRequest("/choices/reorder", {
    body: {
      priorities: choices.map((choice) => ({
        college_code: choice.code,
        branch_code: choice.branchCode,
        category: choice.fitBand,
        notes: choice.notes,
        new_priority: choice.priority,
      })),
    },
    method: "PUT",
  });
}

export function updateChoice(choice) {
  return apiRequest(
    `/choices/${choice.backendId}?category=${encodeURIComponent(choice.fitBand)}&notes=${encodeURIComponent(choice.notes)}`,
    { method: "PUT" },
  );
}

export function addChoice(choice) {
  return apiRequest("/choices/", {
    body: {
      branch_code: choice.branchCode,
      category: choice.fitBand || "Moderate",
      college_code: choice.code,
      notes: choice.notes || "",
      priority: choice.priority || 300,
    },
    method: "POST",
  });
}

export function createChoiceSnapshot(title) {
  return apiRequest("/choices/snapshots", { body: { title }, method: "POST" });
}

export function fetchChoiceSnapshots() {
  return apiRequest("/choices/snapshots");
}

export function restoreChoiceSnapshot(id) {
  return apiRequest(`/choices/snapshots/${id}/restore`, { method: "POST" });
}

export function uploadChoiceCsv(file) {
  const body = new FormData();
  body.append("file", file);
  return apiRequest("/choices/upload", { body, method: "POST" });
}

export async function searchColleges(payload) {
  const rows = await apiRequest("/explore/search", { body: payload, method: "POST" });
  const branch = payload.branch_code
    ? { code: payload.branch_code, name: `${payload.branch_code} branch match` }
    : fallbackBranch;
  return rows.map((row) => buildExploreCollege(row, branch));
}

export async function fetchCollegeDetail(code) {
  return buildCollegeDetail(await apiRequest(`/explore/${encodeURIComponent(code)}`));
}

export function compareColleges(codes, branches) {
  return apiRequest("/compare/", {
    body: { college_codes: codes, branch_codes: branches },
    method: "POST",
  });
}

export async function fetchCompareSessions() {
  const sessions = await apiRequest("/compare/sessions");
  return sessions.map(buildCompareSession);
}

export async function saveCompareSession(payload) {
  return buildCompareSession(await apiRequest("/compare/sessions", { body: payload, method: "POST" }));
}

export function runOnboarding(payload) {
  return apiRequest("/guidance/onboarding", { body: payload, method: "POST" });
}

export async function fetchWorkspaceSettings() {
  return buildWorkspaceSettings(await apiRequest("/workspace/settings"));
}

export async function updateWorkspaceSettings(settings) {
  return buildWorkspaceSettings(await apiRequest("/workspace/settings", {
    body: {
      compact_view: settings.compactView,
      default_district: settings.defaultDistrict || null,
      mobile_density: settings.mobileDensity,
      preferred_branches: settings.preferredBranches,
      theme_mode: settings.themeMode,
    },
    method: "PUT",
  }));
}

// ── Maps API helpers ─────────────────────────────────────────────

export function fetchMapColleges(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiRequest(`/maps/colleges${qs ? `?${qs}` : ""}`);
}

export function fetchTfcLocations(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiRequest(`/maps/tfc-locations${qs ? `?${qs}` : ""}`);
}
