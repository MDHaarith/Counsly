import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRazorpayCheckoutOptions,
  buildVerificationPayload,
  paywallCopyForSource,
} from "../lib/payments.mjs";

test("paywallCopyForSource returns contextual PRD headings and summaries", () => {
  const choices = paywallCopyForSource("choices");
  const recommendations = paywallCopyForSource("recommendations");

  assert.equal(choices.heading, "Choice Filing requires Full Access.");
  assert.match(choices.summary, /snapshots/i);
  assert.equal(recommendations.heading, "Showing 3 of X colleges. Unlock all for ₹149.");
});

test("buildVerificationPayload maps Razorpay modal response to backend verification shape", () => {
  assert.deepEqual(buildVerificationPayload({
    razorpay_order_id: "order_123",
    razorpay_payment_id: "pay_123",
    razorpay_signature: "sig_123",
  }), {
    razorpay_order_id: "order_123",
    razorpay_payment_id: "pay_123",
    razorpay_signature: "sig_123",
  });
});

test("buildRazorpayCheckoutOptions uses the backend order, student prefill, consent copy, and verify handler", async () => {
  let verified = null;
  const options = buildRazorpayCheckoutOptions({
    key: "rzp_test_123",
    order: { amount: 14900, currency: "INR", id: "order_123" },
    source: "choices",
    user: { google_email: "student@example.com", name: "Haarith" },
    verify: async (payload) => {
      verified = payload;
      return { success: true };
    },
  });

  assert.equal(options.key, "rzp_test_123");
  assert.equal(options.amount, 14900);
  assert.equal(options.currency, "INR");
  assert.equal(options.order_id, "order_123");
  assert.equal(options.prefill.email, "student@example.com");
  assert.equal(options.prefill.name, "Haarith");
  assert.match(options.notes.feature, /choices/);

  await options.handler({
    razorpay_order_id: "order_123",
    razorpay_payment_id: "pay_123",
    razorpay_signature: "sig_123",
  });
  assert.deepEqual(verified, {
    razorpay_order_id: "order_123",
    razorpay_payment_id: "pay_123",
    razorpay_signature: "sig_123",
  });
});
