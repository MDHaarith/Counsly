function bytesToHex(buffer) {
  return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function sha256Hex(source) {
  if (!globalThis.crypto?.subtle) return "";
  const buffer = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(source));
  return bytesToHex(buffer);
}

function readTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "";
  } catch {
    return "";
  }
}

export function buildDeviceFingerprintSource(env = {}) {
  const nav = env.navigator || globalThis.navigator || {};
  const screen = env.screen || globalThis.screen || {};
  const timezone = env.timezone ?? readTimezone();
  return [
    `ua=${nav.userAgent || ""}`,
    `lang=${nav.language || ""}`,
    `platform=${nav.platform || ""}`,
    `hw=${nav.hardwareConcurrency || ""}`,
    `screen=${screen.width || ""}x${screen.height || ""}x${screen.colorDepth || ""}`,
    `tz=${timezone || ""}`,
  ].join("|");
}

export function isSha256Hex(value) {
  return /^[a-f0-9]{64}$/.test(String(value || ""));
}

export async function createDeviceFingerprint(env = {}) {
  return sha256Hex(buildDeviceFingerprintSource(env));
}
