import assert from "node:assert/strict";
import test from "node:test";

import { buildRequestHeaders } from "../src/lib/api";

test("preserves Headers entries such as cookie when building request headers", () => {
  const input = new Headers();
  input.set("cookie", "counsly_session=test-token");

  const headers = buildRequestHeaders(input, false);

  assert.equal(headers.get("cookie"), "counsly_session=test-token");
  assert.equal(headers.get("Content-Type"), "application/json");
});
