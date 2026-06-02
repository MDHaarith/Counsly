import assert from "node:assert/strict";
import test from "node:test";

import { submitStep1Eligibility } from "../lib/onboarding-flow.mjs";

test("onboarding wizard remains on step 1 and surfaces backend errors when runOnboarding rejects", async () => {
  const result = await submitStep1Eligibility({
    maths: 95,
    physics: 48,
    chemistry: 47,
    runOnboarding: async () => {
      throw new Error("Workspace environment not initialized");
    },
  });

  assert.equal(result.nextStep, 1);
  assert.equal(result.backendConfirmed, false);
  assert.equal(result.errorMsg, "Workspace environment not initialized");
});

test("onboarding wizard advances only after an eligible backend-confirmed response", async () => {
  const result = await submitStep1Eligibility({
    maths: 95,
    physics: 48,
    chemistry: 47,
    runOnboarding: async () => ({
      eligible: true,
      message: "Eligibility confirmed.",
      onboarding_completed: true,
    }),
  });

  assert.equal(result.nextStep, 2);
  assert.equal(result.backendConfirmed, true);
  assert.equal(result.errorMsg, "");
});


test("onboarding wizard stays on step 1 when backend response is not eligible", async () => {
  const result = await submitStep1Eligibility({
    maths: 40,
    physics: 20,
    chemistry: 17,
    runOnboarding: async () => ({
      eligible: false,
      message: "Aggregate mark below the counseling eligibility threshold.",
      onboarding_completed: false,
    }),
  });

  assert.equal(result.nextStep, 1);
  assert.equal(result.backendConfirmed, false);
  assert.equal(result.errorMsg, "Aggregate mark below the counseling eligibility threshold.");
});
