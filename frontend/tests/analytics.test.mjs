import assert from "node:assert/strict";
import test from "node:test";

import {
  buildFunnelEvent,
  funnelEventNames,
  trackFunnelEvent,
} from "../lib/analytics.mjs";

test("buildFunnelEvent creates PRD funnel events with stable names and context", () => {
  assert.deepEqual(buildFunnelEvent("paywall", {
    feature: "choices",
    user: { id: "usr_123", subscription_active: false },
  }), {
    event: "paywall_seen",
    feature: "choices",
    subscribed: false,
    user_id: "usr_123",
  });
});

test("funnelEventNames exposes every FR-114 step as a distinct event", () => {
  assert.deepEqual(funnelEventNames, {
    collegeAdded: "college_added",
    firstRecommendationViewed: "first_recommendation_viewed",
    onboardingCompleted: "onboarding_completed",
    onboardingStarted: "onboarding_started",
    paymentCompleted: "payment_completed",
    paymentStarted: "payment_started",
    paywallSeen: "paywall_seen",
  });
});

test("trackFunnelEvent sends GA4 gtag events and dataLayer fallback when available", () => {
  const calls = [];
  const win = {
    dataLayer: [],
    gtag: (...args) => calls.push(args),
  };

  const payload = trackFunnelEvent("payment_completed", {
    amount: 14900,
    feature: "rounds",
    user: { id: "usr_456", subscription_active: true },
  }, win);

  assert.equal(payload.event, "payment_completed");
  assert.equal(payload.feature, "rounds");
  assert.equal(payload.amount, 14900);
  assert.equal(payload.subscribed, true);
  assert.deepEqual(calls[0], ["event", "payment_completed", {
    amount: 14900,
    feature: "rounds",
    subscribed: true,
    user_id: "usr_456",
  }]);
  assert.deepEqual(win.dataLayer[0], payload);
});
