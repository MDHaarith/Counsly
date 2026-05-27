import assert from "node:assert/strict";
import test from "node:test";

// Mock the browser globals for Node.js environment so the API helper handles state properly
const storage = new Map();
globalThis.window = {
  sessionStorage: {
    getItem: (key) => storage.get(key) || null,
    setItem: (key, val) => storage.set(key, val),
    removeItem: (key) => storage.delete(key),
  },
  localStorage: {
    getItem: () => null,
    removeItem: () => {},
  }
};

// Set the API base URL to our local test server
process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000";

import {
  apiRequest,
  fetchChoices,
  getStoredToken,
  startSession,
} from "../lib/api.mjs";

test("Full-Stack Student Lifecycle Integration Flow", async () => {
  // 1. Authenticate using developer Google OAuth fallback mode
  console.log("Step 1: Starting dev-auth fallback session...");
  const sessionResult = await startSession({
    google_email: "test.student@example.com",
    name: "Test Student",
    device_fingerprint_hash: "mock_fingerprint_hash_abc123",
  });

  assert.ok(sessionResult.access_token, "Access token must be returned.");
  assert.ok(getStoredToken(), "Access token must be saved to mock sessionStorage.");
  console.log("✓ Session active. Token retrieved.");

  // 2. Submit onboarding marks (maths/physics/chemistry) -> Confirm eligibility
  console.log("Step 2: Submitting onboarding marks...");
  const onboardingResult = await apiRequest("/guidance/onboarding", {
    method: "POST",
    body: {
      maths: 98,
      physics: 48,
      chemistry: 47,
      preferred_branches: ["CS", "IT"],
      default_district: "Chennai",
    },
  });

  assert.equal(onboardingResult.eligible, true, "Student should be eligible with high marks.");
  console.log("✓ Onboarding completed. Eligibility confirmed.");

  // 3. Fetch initial choice list (should be empty initially)
  console.log("Step 3: Checking initial choice list...");
  const initialChoices = await fetchChoices();
  assert.ok(Array.isArray(initialChoices), "Choices must be returned as an array.");
  const countBefore = initialChoices.length;
  console.log(`✓ Initial choices loaded. Count: ${countBefore}`);

  try {
    const addResult = await apiRequest("/choices/", {
      method: "POST",
      body: {
        college_code: "1",
        branch_code: "AD",
        priority: 1,
        category: "Safe",
        notes: "Top option",
      },
    });
    assert.ok(addResult.id, "Newly created choice preference must have an ID.");
  } catch (err) {
    console.error("Step 4 failed with error details:", err.message);
    throw err;
  }
  console.log("✓ Choice successfully filed.");

  // 5. Verify the choice list now contains the added preference
  console.log("Step 5: Verifying choice list updates...");
  const updatedChoices = await fetchChoices();
  assert.equal(updatedChoices.length, countBefore + 1, "Choice count should have incremented.");
  const addedChoice = updatedChoices.find(c => c.branchCode === "AD");
  assert.ok(addedChoice, "AIDS choice must exist in list.");
  console.log("✓ Choices list verification passed.");

  // 6. Test Snapshots flow (saving and restoring)
  console.log("Step 6: Creating a shortlist snapshot...");
  const snapshotResult = await apiRequest("/choices/snapshots", {
    method: "POST",
    body: {
      title: "My First Safe List",
    },
  });
  assert.ok(snapshotResult.id, "Snapshot ID must be generated.");
  assert.equal(snapshotResult.title, "My First Safe List");
  console.log("✓ Shortlist snapshot successfully created.");

  // 7. Confirm deterministic compare remains available in the free student workflow.
  console.log("Step 7: Running deterministic college compare...");
  const compareResult = await apiRequest("/compare/", {
    method: "POST",
    body: {
      college_codes: ["1", "4"],
      branch_codes: ["AD", "CS"],
    },
  });
  assert.ok(compareResult.explanation, "Compare explanation must be generated.");
  assert.ok(compareResult.colleges.length >= 2, "Compare must return at least two colleges.");
  console.log("✓ Deterministic compare completed.");
});
