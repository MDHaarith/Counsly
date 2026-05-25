import assert from "node:assert/strict";
import test from "node:test";

import { buildChoiceExportModel } from "../lib/choice-export.mjs";

test("buildChoiceExportModel includes student context, ordered rows, notes, and disclaimer", () => {
  const model = buildChoiceExportModel({
    choices: [
      { branchCode: "CS", branchName: "CSE", code: "0001", fitBand: "Ambitious", name: "CEG", notes: "Dream row.", priority: 1 },
    ],
    exportedAt: new Date("2026-05-23T00:00:00Z"),
    student: { chemistry: 49, community: "OC", maths: 98, name: "Haarith", physics: 49 },
  });

  assert.equal(model.title, "Counsly TNEA Choice List");
  assert.match(model.meta[0], /Haarith/);
  assert.match(model.meta[1], /196/);
  assert.deepEqual(model.rows[0], ["1", "0001 CEG", "CS CSE", "Ambitious", "Dream row."]);
  assert.match(model.disclaimer, /not a guarantee/i);
});
