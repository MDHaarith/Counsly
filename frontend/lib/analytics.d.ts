export const funnelEventNames: {
  collegeAdded: string;
  firstRecommendationViewed: string;
  onboardingCompleted: string;
  onboardingStarted: string;
};

export function buildFunnelEvent(name: string, context?: Record<string, unknown>): Record<string, unknown>;

export function trackFunnelEvent(name: string, context?: Record<string, unknown>, win?: Window): Record<string, unknown>;
