import assert from "node:assert/strict";
import test from "node:test";

import {
  buildDeviceFingerprintSource,
  createDeviceFingerprint,
  isSha256Hex,
} from "../lib/device-fingerprint.mjs";

test("buildDeviceFingerprintSource uses non-PII device traits for abuse prevention", () => {
  const source = buildDeviceFingerprintSource({
    navigator: {
      hardwareConcurrency: 8,
      language: "en-IN",
      platform: "Linux x86_64",
      userAgent: "Mozilla/5.0 Test",
    },
    screen: {
      colorDepth: 24,
      height: 1080,
      width: 1920,
    },
    timezone: "Asia/Calcutta",
  });

  assert.equal(source, "ua=Mozilla/5.0 Test|lang=en-IN|platform=Linux x86_64|hw=8|screen=1920x1080x24|tz=Asia/Calcutta");
  assert.equal(source.includes("@"), false);
});

test("createDeviceFingerprint returns a SHA-256 hex digest", async () => {
  const fingerprint = await createDeviceFingerprint({
    navigator: {
      hardwareConcurrency: 8,
      language: "en-IN",
      platform: "Linux x86_64",
      userAgent: "Mozilla/5.0 Test",
    },
    screen: {
      colorDepth: 24,
      height: 1080,
      width: 1920,
    },
    timezone: "Asia/Calcutta",
  });

  assert.equal(isSha256Hex(fingerprint), true);
  assert.equal(fingerprint.length, 64);
});
