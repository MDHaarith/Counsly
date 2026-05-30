import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../app/profile/edit/page.tsx", import.meta.url), "utf8");

test("profile editor uses plain official-form controls instead of flashy dashboard widgets", () => {
  assert.equal(source.includes('type="range"'), false);
  assert.equal(source.includes("Tactile Sliders"), false);
  assert.equal(source.includes("Premium"), false);
  assert.equal(source.includes("Calibrated"), false);
  assert.equal(source.includes("rounded-full border-4"), false);
  assert.equal(source.includes("bg-gradient-to-b"), false);
});
