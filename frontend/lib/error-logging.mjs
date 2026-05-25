function nowIso() {
  return new Date().toISOString();
}

function bytesToHex(buffer) {
  return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function hashUserId(userId = "anonymous") {
  const source = String(userId || "anonymous");
  if (!globalThis.crypto?.subtle) return `unhashed:${source}`;
  const buffer = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(source));
  return bytesToHex(buffer);
}

export function shouldLogApiError(status) {
  return Number(status) >= 500;
}

export function readStoredUser(win = globalThis.window) {
  if (!win?.sessionStorage && !win?.localStorage) return null;
  try {
    const sessionValue = win.sessionStorage?.getItem("counsly_user");
    if (sessionValue) return JSON.parse(sessionValue);

    const legacyValue = win.localStorage?.getItem("counsly_user");
    if (!legacyValue) return null;

    win.sessionStorage?.setItem("counsly_user", legacyValue);
    win.localStorage?.removeItem("counsly_user");
    return JSON.parse(legacyValue);
  } catch {
    return null;
  }
}

export async function buildApiErrorLog({
  endpoint,
  errorType = "server_error",
  message = "",
  status,
  timestamp = nowIso(),
  userId,
} = {}) {
  return {
    endpoint,
    error_type: errorType,
    kind: "api_error",
    message,
    status,
    timestamp,
    user_id_hash: await hashUserId(userId),
  };
}

export async function buildClientErrorLog({
  error,
  message,
  route = "",
  timestamp = nowIso(),
  userId,
} = {}) {
  const normalized = error instanceof Error ? error : null;
  return {
    endpoint: route,
    error_type: normalized?.name || "ClientError",
    kind: "client_js_error",
    message: normalized?.message || message || "Client-side error",
    stack: normalized?.stack || "",
    timestamp,
    user_id_hash: await hashUserId(userId),
  };
}

export async function submitErrorLog(payload, fetcher = globalThis.fetch, baseUrl = "") {
  if (typeof fetcher !== "function") return;
  try {
    await fetcher(`${baseUrl}/logging/client-error`, {
      body: JSON.stringify(payload),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
  } catch {
    // Error reporting must never break the user flow.
  }
}

export async function logApiError(input, options = {}) {
  const payload = await buildApiErrorLog(input);
  await submitErrorLog(payload, options.fetcher, options.baseUrl);
  return payload;
}

export async function logClientError(input, options = {}) {
  const payload = await buildClientErrorLog(input);
  await submitErrorLog(payload, options.fetcher, options.baseUrl);
  return payload;
}

/**
 * @param {{ baseUrl?: string, userId?: string, win?: Window }} [options]
 */
export function installClientErrorHandlers(options = {}) {
  const { baseUrl = "", userId, win = globalThis.window } = options;
  if (!win?.addEventListener) return;
  win.__counsly_error_logging_user_id = userId;
  if (win.__counsly_error_logging_installed) return;
  win.__counsly_error_logging_installed = true;

  win.addEventListener("error", (event) => {
    void logClientError({
      error: event.error,
      message: event.message,
      route: win.location?.pathname || "",
      userId: win.__counsly_error_logging_user_id,
    }, { baseUrl });
  });

  win.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason instanceof Error ? event.reason : new Error(String(event.reason || "Unhandled promise rejection"));
    void logClientError({
      error: reason,
      route: win.location?.pathname || "",
      userId: win.__counsly_error_logging_user_id,
    }, { baseUrl });
  });
}
