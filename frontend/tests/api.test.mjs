import assert from "node:assert/strict";
import test from "node:test";

import {
  apiRequest,
  buildChoiceRow,
  buildCompareSession,
  buildExploreCollege,
  buildOperationalStatus,
  buildRequestInit,
  buildWorkspaceSettings,
  toDecisionType,
} from "../lib/api.mjs";

test("buildChoiceRow maps backend choice metadata into filing rows", () => {
  const choice = buildChoiceRow({
    id: 42,
    college_code: "0001",
    branch_code: "CS",
    priority: 3,
    category: "Ambitious",
    notes: "Keep above local backups.",
    college_name: "College of Engineering, Guindy",
    branch_name: "Computer Science and Engineering",
    fee_structure_annual: 25000,
    placement_rate_pct: 98,
  });

  assert.equal(choice.id, "choice-42");
  assert.equal(choice.code, "0001");
  assert.equal(choice.branchCode, "CS");
  assert.equal(choice.fitBand, "Ambitious");
  assert.equal(choice.notes, "Keep above local backups.");
  assert.equal(choice.fees, 25000);
});

test("buildExploreCollege preserves fit ranking and fills branch preview defaults", () => {
  const college = buildExploreCollege({
    code: "2006",
    name: "PSG College of Technology",
    district: "Coimbatore",
    type: "Aided",
    is_autonomous: true,
    fee_structure_annual: 85000,
    placement_rate_pct: 96,
    fit_score: 95.4,
  });

  assert.equal(college.code, "2006");
  assert.equal(college.branchCode, "CS");
  assert.equal(college.fitScore, 95.4);
  assert.equal(college.fitBand, "Safe");
  assert.equal(college.transport, false);
});

test("buildRequestInit carries bearer tokens and JSON bodies", () => {
  const init = buildRequestInit(
    { body: { college_codes: ["0001", "2006"], branch_codes: ["CS", "IT"] }, method: "POST" },
    "token-123",
  );

  assert.equal(init.method, "POST");
  assert.equal(init.headers.Authorization, "Bearer token-123");
  assert.equal(init.headers["Content-Type"], "application/json");
  assert.equal(init.body, JSON.stringify({ college_codes: ["0001", "2006"], branch_codes: ["CS", "IT"] }));
});

test("apiRequest logs 5xx failures to the client logging endpoint", async () => {
  const previousFetch = globalThis.fetch;
  const previousWindow = globalThis.window;
  const calls = [];
  globalThis.window = {
    localStorage: {
      getItem() {
        return "";
      },
      removeItem() {},
    },
    sessionStorage: {
      getItem(key) {
        if (key === "counsly_user") return JSON.stringify({ id: "usr_123" });
        return "";
      },
      removeItem() {},
      setItem() {},
    },
  };
  globalThis.fetch = async (url, init) => {
    calls.push({ init, url });
    if (String(url).endsWith("/logging/client-error")) return { ok: true, json: async () => ({}) };
    return {
      ok: false,
      status: 500,
      json: async () => ({ detail: "Database unavailable" }),
    };
  };

  await assert.rejects(() => apiRequest("/choices/"), /Database unavailable/);

  assert.equal(calls.length, 2);
  assert.equal(calls[1].url, "/logging/client-error");
  const logged = JSON.parse(calls[1].init.body);
  assert.equal(logged.kind, "api_error");
  assert.equal(logged.endpoint, "/choices/");
  assert.equal(logged.status, 500);
  assert.equal(logged.user_id_hash, "ca010ec7feb32be7e30002f602d7c2ab062fb7a2be105ae6b8b1fb739cb72c77");

  globalThis.fetch = previousFetch;
  globalThis.window = previousWindow;
});

test("buildCompareSession maps saved compare sessions to resume URLs", () => {
  const session = buildCompareSession({
    id: 8,
    session_name: "CEG vs PSG",
    college_codes: ["0001", "2006"],
    branch_codes: ["CS", "IT"],
    created_at: "2026-05-23T00:00:00",
  });

  assert.equal(session.id, "compare-8");
  assert.equal(session.title, "CEG vs PSG");
  assert.equal(session.href, "/compare?ids=0001%2C2006&branches=CS%2CIT");
});

test("buildWorkspaceSettings normalizes backend defaults for profile forms", () => {
  const settings = buildWorkspaceSettings({
    default_district: "Coimbatore",
    preferred_branches: ["CS", "IT"],
    compact_view: true,
    mobile_density: "compact",
  });

  assert.equal(settings.defaultDistrict, "Coimbatore");
  assert.deepEqual(settings.preferredBranches, ["CS", "IT"]);
  assert.equal(settings.compactView, true);
  assert.equal(settings.mobileDensity, "compact");
});

test("buildOperationalStatus maps admin and scraping state without news", () => {
  const status = buildOperationalStatus({
    admin_updates: [{ dataset: "cutoff_data", status: "needs_review" }],
    scraping_jobs: [{ dataset: "seat_matrix", status: "success" }],
    ai: { configured: false },
  });

  assert.equal(status.adminUpdates[0].dataset, "cutoff_data");
  assert.equal(status.scrapingJobs[0].dataset, "seat_matrix");
  assert.equal(status.ai.configured, false);
  assert.equal(Object.keys(status).includes("news"), false);
});
