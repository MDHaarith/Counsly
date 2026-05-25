export const funnelEventNames = {
  collegeAdded: "college_added",
  firstRecommendationViewed: "first_recommendation_viewed",
  onboardingCompleted: "onboarding_completed",
  onboardingStarted: "onboarding_started",
  paymentCompleted: "payment_completed",
  paymentStarted: "payment_started",
  paywallSeen: "paywall_seen",
};

const aliases = {
  college_added: funnelEventNames.collegeAdded,
  collegeAdded: funnelEventNames.collegeAdded,
  first_recommendation_viewed: funnelEventNames.firstRecommendationViewed,
  firstRecommendationViewed: funnelEventNames.firstRecommendationViewed,
  onboarding_completed: funnelEventNames.onboardingCompleted,
  onboarding_started: funnelEventNames.onboardingStarted,
  onboardingCompleted: funnelEventNames.onboardingCompleted,
  onboardingStarted: funnelEventNames.onboardingStarted,
  payment_completed: funnelEventNames.paymentCompleted,
  payment_started: funnelEventNames.paymentStarted,
  paymentCompleted: funnelEventNames.paymentCompleted,
  paymentStarted: funnelEventNames.paymentStarted,
  paywall: funnelEventNames.paywallSeen,
  paywall_seen: funnelEventNames.paywallSeen,
  paywallSeen: funnelEventNames.paywallSeen,
};

function resolveName(name) {
  return aliases[name] || name;
}

function safeUserId(user) {
  return user?.id || "anonymous";
}

export function buildFunnelEvent(name, context = {}) {
  const { user, ...rest } = context;
  return {
    event: resolveName(name),
    ...rest,
    subscribed: Boolean(user?.subscription_active),
    user_id: safeUserId(user),
  };
}

export function trackFunnelEvent(name, context = {}, win = globalThis.window) {
  const payload = buildFunnelEvent(name, context);
  if (!win) return payload;

  if (typeof win.gtag === "function") {
    const { event, ...params } = payload;
    win.gtag("event", event, params);
  }

  if (Array.isArray(win.dataLayer)) {
    win.dataLayer.push(payload);
  }

  return payload;
}
