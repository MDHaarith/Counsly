export const DEVELOPMENT_GOOGLE_CLIENT_IDS = new Set([
  "dev",
  "development",
  "mock",
  "mock-dev-client-id",
  "test",
]);

export function normalizeGoogleClientId(clientId = "") {
  return String(clientId || "").trim();
}

export function isDevelopmentGoogleClientId(clientId = "") {
  const normalizedClientId = normalizeGoogleClientId(clientId);
  return DEVELOPMENT_GOOGLE_CLIENT_IDS.has(normalizedClientId);
}

export function hasRealGoogleClientId(clientId = "") {
  const normalizedClientId = normalizeGoogleClientId(clientId);

  return Boolean(normalizedClientId) && normalizedClientId.endsWith(".apps.googleusercontent.com");
}

export function shouldRenderManualLoginForm(clientId = "") {
  const normalizedClientId = normalizeGoogleClientId(clientId);
  return !normalizedClientId || isDevelopmentGoogleClientId(normalizedClientId);
}
