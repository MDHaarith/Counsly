import assert from "node:assert/strict";
import test from "node:test";

import { choiceWriteDestination, paidFeatureDestination } from "../lib/access.mjs";

test("paidFeatureDestination allows all screens under free algorithmic cycle", () => {
  assert.equal(paidFeatureDestination("/choices"), "");
  assert.equal(paidFeatureDestination("/analytics"), "");
  assert.equal(paidFeatureDestination("/recommendations"), "");
  assert.equal(paidFeatureDestination("/compare"), "");
});

test("choiceWriteDestination leaves mutating actions fully open for all students", () => {
  assert.equal(choiceWriteDestination({}, "recommendations"), "");
  assert.equal(choiceWriteDestination({}, "explore"), "");
});
