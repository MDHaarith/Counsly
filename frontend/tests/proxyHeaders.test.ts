import assert from "node:assert/strict";
import test from "node:test";

import { cloneProxyResponseHeaders } from "../src/lib/proxyHeaders";

test("preserves multiple set-cookie headers from upstream responses", () => {
  const upstreamHeaders = new Headers();
  upstreamHeaders.set("location", "https://counsly-frontend.vercel.app/dashboard");
  upstreamHeaders.append("set-cookie", "counsly_session=session-token; Path=/; HttpOnly; SameSite=Lax");
  upstreamHeaders.append("set-cookie", "counsly_oauth_state=\"\"; Max-Age=0; Path=/; HttpOnly; SameSite=Lax");

  const responseHeaders = cloneProxyResponseHeaders(upstreamHeaders);

  assert.equal(responseHeaders.get("location"), "https://counsly-frontend.vercel.app/dashboard");
  assert.deepEqual(responseHeaders.getSetCookie(), [
    "counsly_session=session-token; Path=/; HttpOnly; SameSite=Lax",
    'counsly_oauth_state=""; Max-Age=0; Path=/; HttpOnly; SameSite=Lax',
  ]);
});
