import assert from "node:assert/strict";
import test from "node:test";

import { inventoryRoutes, navItems } from "../lib/navigation.mjs";

test("product inventory exposes every active 2027 frontend route", () => {
  assert.deepEqual(
    inventoryRoutes,
    [
      "/",
      "/login",
      "/subscribe",
      "/onboarding/marks",
      "/onboarding/details",
      "/dashboard",
      "/recommendations",
      "/choices",
      "/analytics",
      "/rounds",
      "/explore",
      "/explore/[code]",
      "/compare",
      "/profile/edit",
      "/admin",
    ],
  );
});

test("authenticated navigation keeps the primary student workflow visible", () => {
  assert.deepEqual(
    navItems.map((item) => item.href),
    [
      "/dashboard",
      "/recommendations",
      "/choices",
      "/analytics",
      "/rounds",
      "/explore",
      "/profile/edit",
    ],
  );
});

test("navigation does not expose a news or alerts module", () => {
  assert.equal(inventoryRoutes.some((route) => route.includes("news")), false);
  assert.equal(navItems.some((item) => /news|alert/i.test(`${item.href} ${item.label} ${item.longLabel}`)), false);
});
