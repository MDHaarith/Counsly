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

test("Full-Stack Student Lifecycle Integration Flow", async () => {
  // Ensure NEXT_PUBLIC_API_BASE_URL is set before importing the API client dynamically
  if (!process.env.NEXT_PUBLIC_API_BASE_URL) {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000";
  }

  // Import API module dynamically to ensure process.env changes are fully propagated
  const {
    startSession,
    runOnboarding,
    fetchChoices,
    addChoice,
    createChoiceSnapshot,
    compareColleges,
    getStoredToken,
  } = await import("../lib/api.mjs");

  // 1. Authenticate using developer Google OAuth fallback mode
  console.log("Step 1: Starting dev-auth fallback session...");
  const uniqueEmail = `test.student-${Date.now()}@example.com`;
  const uniqueFingerprint = `mock_fingerprint_hash_${Date.now()}`;
  const sessionResult = await startSession({
    google_email: uniqueEmail,
    name: "Test Student",
    device_fingerprint_hash: uniqueFingerprint,
  });

  assert.ok(sessionResult.access_token, "Access token must be returned.");
  assert.ok(getStoredToken(), "Access token must be saved to mock sessionStorage.");
  console.log("✓ Session active. Token retrieved.");

  // 2. Submit onboarding marks (maths/physics/chemistry) -> Confirm eligibility
  console.log("Step 2: Submitting onboarding marks...");
  const onboardingResult = await runOnboarding({
    maths: 98,
    physics: 48,
    chemistry: 47,
    preferred_branches: ["CS", "IT"],
    default_district: "Chennai",
  });

  assert.equal(onboardingResult.eligible, true, "Student should be eligible with high marks.");
  console.log("✓ Onboarding completed. Eligibility confirmed.");

  // 3. Fetch initial choice list (should be empty initially)
  console.log("Step 3: Checking initial choice list...");
  const initialChoices = await fetchChoices();
  assert.ok(Array.isArray(initialChoices), "Choices must be returned as an array.");
  const countBefore = initialChoices.length;
  console.log(`✓ Initial choices loaded. Count: ${countBefore}`);

  // 4. File a choice preference using public connector
  console.log("Step 4: Filing a choice preference...");
  try {
    const addResult = await addChoice({
      code: "1",
      branchCode: "CS",
      priority: 1,
      fitBand: "Safe",
      notes: "Top option",
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
  const addedChoice = updatedChoices.find(c => c.branchCode === "CS");
  assert.ok(addedChoice, "CS choice must exist in list.");
  console.log("✓ Choices list verification passed.");

  // 6. Test Snapshots flow (saving and restoring) using public snapshot connector
  console.log("Step 6: Creating a shortlist snapshot...");
  const snapshotResult = await createChoiceSnapshot("My First Safe List");
  assert.ok(snapshotResult.id, "Snapshot ID must be generated.");
  assert.equal(snapshotResult.title, "My First Safe List");
  console.log("✓ Shortlist snapshot successfully created.");

  // 7. Confirm deterministic compare remains available in the free student workflow using compare colleges connector
  console.log("Step 7: Running deterministic college compare...");
  const compareResult = await compareColleges(["1", "4"], ["CS", "CS"]);
  assert.ok(compareResult.explanation, "Compare explanation must be generated.");
  assert.ok(compareResult.colleges.length >= 2, "Compare must return at least two colleges.");
  console.log("✓ Deterministic compare completed.");
});
