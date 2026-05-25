import assert from "node:assert/strict";
import test from "node:test";

import { choiceWriteDestination, paidFeatureDestination } from "../lib/access.mjs";

test("paidFeatureDestination routes hard-gated paid screens to contextual paywalls", () => {
  assert.equal(paidFeatureDestination("/choices"), "/subscribe?from=choices");
  assert.equal(paidFeatureDestination("/analytics"), "/subscribe?from=analytics");
});

test("paidFeatureDestination leaves free and soft-gated screens open", () => {
  assert.equal(paidFeatureDestination("/recommendations"), "");
  assert.equal(paidFeatureDestination("/compare"), "");
  assert.equal(paidFeatureDestination("/explore/0001"), "");
});

test("choiceWriteDestination blocks free users from mutating the paid choice list", () => {
  assert.equal(choiceWriteDestination({ subscription_active: false }, "recommendations"), "/subscribe?from=recommendations");
  assert.equal(choiceWriteDestination({ subscription_active: true }, "explore"), "");
});
