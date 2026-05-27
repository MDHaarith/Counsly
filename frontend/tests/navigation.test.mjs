import assert from "node:assert/strict";
import test from "node:test";

import { inventoryRoutes, navItems } from "../lib/navigation.mjs";

test("product inventory exposes every active 2027 PDF route", () => {
  assert.deepEqual(
    inventoryRoutes,
    [
      "/",
      "/login",
      "/onboarding/marks",
      "/onboarding/details",
      "/dashboard",
      "/recommendations",
      "/choices",
      "/explore",
      "/explore/[code]",
      "/compare",
      "/maps",
      "/profile/edit",
    ],
  );
});

test("authenticated navigation keeps the PDF student workflow visible", () => {
  assert.deepEqual(
    navItems.map((item) => item.href),
    [
      "/dashboard",
      "/recommendations",
      "/choices",
      "/compare",
      "/explore",
      "/maps",
      "/profile/edit",
    ],
  );
});
