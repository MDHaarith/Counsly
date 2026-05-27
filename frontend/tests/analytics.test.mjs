import assert from "node:assert/strict";
import test from "node:test";

import {
  buildFunnelEvent,
  funnelEventNames,
  trackFunnelEvent,
} from "../lib/analytics.mjs";

test("buildFunnelEvent creates PRD funnel events with stable names and context", () => {
  assert.deepEqual(buildFunnelEvent("college_added", {
    source: "choices",
    user: { id: "usr_123" },
  }), {
    event: "college_added",
    source: "choices",
    user_id: "usr_123",
  });
});

test("funnelEventNames exposes every FR-114 step as a distinct event", () => {
  assert.deepEqual(funnelEventNames, {
    collegeAdded: "college_added",
    firstRecommendationViewed: "first_recommendation_viewed",
    onboardingCompleted: "onboarding_completed",
    onboardingStarted: "onboarding_started",
  });
});

test("trackFunnelEvent sends GA4 gtag events and dataLayer fallback when available", () => {
  const calls = [];
  const win = {
    dataLayer: [],
    gtag: (...args) => calls.push(args),
  };

  const payload = trackFunnelEvent("first_recommendation_viewed", {
    branch: "CS",
    user: { id: "usr_456" },
  }, win);

  assert.equal(payload.event, "first_recommendation_viewed");
  assert.equal(payload.branch, "CS");
  assert.deepEqual(calls[0], ["event", "first_recommendation_viewed", {
    branch: "CS",
    user_id: "usr_456",
  }]);
  assert.deepEqual(win.dataLayer[0], payload);
});
