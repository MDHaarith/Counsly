export const funnelEventNames = {
  collegeAdded: "college_added",
  firstRecommendationViewed: "first_recommendation_viewed",
  onboardingCompleted: "onboarding_completed",
  onboardingStarted: "onboarding_started",
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
