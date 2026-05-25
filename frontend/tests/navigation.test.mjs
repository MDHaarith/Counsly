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
      "/dataset",
      "/financials",
      "/trends",
      "/maps",
      "/notifications",
      "/reporting",
      "/data-versions",
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
      "/compare",
      "/explore",
      "/analytics",
      "/dataset",
      "/financials",
      "/trends",
      "/maps",
      "/rounds",
      "/notifications",
      "/reporting",
      "/data-versions",
      "/admin",
      "/profile/edit",
    ],
  );
});

test("navigation does not expose a news module", () => {
  assert.equal(inventoryRoutes.some((route) => route.includes("news")), false);
  assert.equal(navItems.some((item) => /news/i.test(`${item.href} ${item.label} ${item.longLabel}`)), false);
  // Notifications/alerts are workspace system events, not a news module — verify they exist
  assert.equal(navItems.some((item) => item.href === "/notifications"), true);
});