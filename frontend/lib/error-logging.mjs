function nowIso() {
  return new Date().toISOString();
}

function bytesToHex(buffer) {
  return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function sha256Fallback(str) {
  const rotateRight = (n, x) => (x >>> n) | (x << (32 - n));
  const choice = (x, y, z) => (x & y) ^ (~x & z);
  const majority = (x, y, z) => (x & y) ^ (x & z) ^ (y & z);
  
  const K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  let words = [];
  const utf8 = unescape(encodeURIComponent(str));
  for (let i = 0; i < utf8.length; i++) {
    words[i >> 2] |= utf8.charCodeAt(i) << (24 - (i % 4) * 8);
  }
  const lenBits = utf8.length * 8;
  words[utf8.length >> 2] |= 0x80 << (24 - (utf8.length % 4) * 8);
  words[(((utf8.length + 8) >> 6) + 1 << 4) - 1] = lenBits;

  let H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];

  for (let i = 0; i < words.length; i += 16) {
    let w = words.slice(i, i + 16);
    for (let j = 16; j < 64; j++) {
      let s0 = rotateRight(7, w[j - 15]) ^ rotateRight(18, w[j - 15]) ^ (w[j - 15] >>> 3);
      let s1 = rotateRight(17, w[j - 2]) ^ rotateRight(19, w[j - 2]) ^ (w[j - 2] >>> 10);
      w[j] = (w[j - 16] + s0 + w[j - 7] + s1) | 0;
    }

    let [a, b, c, d, e, f, g, h] = H;
    for (let j = 0; j < 64; j++) {
      let S1 = rotateRight(6, e) ^ rotateRight(11, e) ^ rotateRight(25, e);
      let ch = choice(e, f, g);
      let temp1 = (h + S1 + ch + K[j] + w[j]) | 0;
      let S0 = rotateRight(2, a) ^ rotateRight(13, a) ^ rotateRight(22, a);
      let maj = majority(a, b, c);
      let temp2 = (S0 + maj) | 0;
      h = g;
      g = f;
      f = e;
      e = (d + temp1) | 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) | 0;
    }

    H = H.map((val, idx) => (val + [a, b, c, d, e, f, g, h][idx]) | 0);
  }

  return H.map(x => (x >>> 0).toString(16).padStart(8, "0")).join("");
}

export function scrubSensitiveData(text) {
  if (typeof text !== "string") return text;
  return text
    .replace(/(eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})/g, "[JWT_REDACTED]")
    .replace(/(Bearer\s+[a-zA-Z0-9_\-\.\/]+)/gi, "Bearer [TOKEN_REDACTED]")
    .replace(/(Authorization\s*:\s*[^\r\n,]+)/gi, "Authorization: [REDACTED]")
    .replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, "[EMAIL_REDACTED]")
    .replace(/(roll_number\s*=\s*[a-zA-Z0-9]+)/gi, "roll_number=[REDACTED]")
    .replace(/(mobile\s*=\s*[0-9]+)/gi, "mobile=[REDACTED]");
}

export async function hashUserId(userId = "anonymous") {
  const source = String(userId || "anonymous");
  if (!globalThis.crypto?.subtle) {
    try {
      return sha256Fallback(source);
    } catch {
      return `unhashed:${source}`;
    }
  }
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
    message: scrubSensitiveData(message),
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
    message: scrubSensitiveData(normalized?.message || message || "Client-side error"),
    stack: scrubSensitiveData(normalized?.stack || ""),
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
