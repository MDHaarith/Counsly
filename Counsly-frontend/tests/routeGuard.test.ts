import assert from "node:assert/strict";
import test from "node:test";

import { getRouteGuardAction } from "../src/lib/routeGuard";

test("redirects unauthenticated auth routes to login", () => {
  assert.deepEqual(getRouteGuardAction("/dashboard", false, false), {
    kind: "redirect",
    pathname: "/login",
    next: "/dashboard",
  });
  assert.deepEqual(getRouteGuardAction("/onboarding/marks", false, false), {
    kind: "redirect",
    pathname: "/login",
    next: "/onboarding/marks",
  });
});

test("allows authenticated auth routes", () => {
  assert.deepEqual(getRouteGuardAction("/choices", true, false), { kind: "next" });
});

test("passes through public and static routes", () => {
  assert.deepEqual(getRouteGuardAction("/", false, false), { kind: "next" });
  assert.deepEqual(getRouteGuardAction("/subscribe", false, false), { kind: "next" });
  assert.deepEqual(getRouteGuardAction("/api/config/status", false, false), { kind: "next" });
  assert.deepEqual(getRouteGuardAction("/_next/static/chunk.js", false, false), { kind: "next" });
  assert.deepEqual(getRouteGuardAction("/health", false, false), { kind: "next" });
});
