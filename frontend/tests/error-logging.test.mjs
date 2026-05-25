import assert from "node:assert/strict";
import test from "node:test";

import {
  buildApiErrorLog,
  buildClientErrorLog,
  hashUserId,
  shouldLogApiError,
  submitErrorLog,
} from "../lib/error-logging.mjs";

test("hashUserId returns a SHA-256 user hash for FR-115 payloads", async () => {
  assert.equal(
    await hashUserId("usr_123"),
    "ca010ec7feb32be7e30002f602d7c2ab062fb7a2be105ae6b8b1fb739cb72c77",
  );
});

test("buildApiErrorLog captures endpoint, type, hashed user id, and timestamp for 5xx errors", async () => {
  const payload = await buildApiErrorLog({
    endpoint: "/choices/",
    errorType: "server_error",
    message: "Backend request failed (500).",
    status: 500,
    timestamp: "2026-05-23T09:30:00.000Z",
    userId: "usr_123",
  });

  assert.equal(payload.kind, "api_error");
  assert.equal(payload.endpoint, "/choices/");
  assert.equal(payload.status, 500);
  assert.equal(payload.error_type, "server_error");
  assert.equal(payload.user_id_hash, "ca010ec7feb32be7e30002f602d7c2ab062fb7a2be105ae6b8b1fb739cb72c77");
  assert.equal(payload.timestamp, "2026-05-23T09:30:00.000Z");
});

test("buildClientErrorLog captures client-side JS error context", async () => {
  const payload = await buildClientErrorLog({
    error: new Error("Render failed"),
    route: "/dashboard",
    timestamp: "2026-05-23T09:31:00.000Z",
    userId: "usr_123",
  });

  assert.equal(payload.kind, "client_js_error");
  assert.equal(payload.endpoint, "/dashboard");
  assert.equal(payload.error_type, "Error");
  assert.equal(payload.message, "Render failed");
  assert.match(payload.stack, /Render failed/);
});

test("shouldLogApiError only logs 5xx responses", () => {
  assert.equal(shouldLogApiError(500), true);
  assert.equal(shouldLogApiError(503), true);
  assert.equal(shouldLogApiError(403), false);
  assert.equal(shouldLogApiError(404), false);
});

test("submitErrorLog posts to the logging endpoint without throwing on failure", async () => {
  const calls = [];
  const fetcher = async (url, init) => {
    calls.push({ init, url });
    return { ok: true };
  };

  await submitErrorLog({ kind: "api_error", endpoint: "/x" }, fetcher, "http://api.test");

  assert.equal(calls[0].url, "http://api.test/logging/client-error");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(calls[0].init.headers["Content-Type"], "application/json");
  assert.equal(calls[0].init.body, JSON.stringify({ kind: "api_error", endpoint: "/x" }));
});
