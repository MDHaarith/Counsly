import assert from "node:assert/strict";
import test from "node:test";

import { hasRealGoogleClientId, shouldRenderManualLoginForm } from "../lib/auth-config.mjs";

test("hasRealGoogleClientId hides manual login for a configured Google OAuth client", () => {
  const realClientId = "1234567890-abcdef.apps.googleusercontent.com";

  assert.equal(hasRealGoogleClientId(realClientId), true);
  assert.equal(shouldRenderManualLoginForm(realClientId), false);
});

test("hasRealGoogleClientId keeps manual login available only for missing or dev/mock client IDs", () => {
  for (const clientId of ["", "   ", "mock-dev-client-id", "development", "dev", "mock", "test"]) {
    assert.equal(hasRealGoogleClientId(clientId), false);
    assert.equal(shouldRenderManualLoginForm(clientId), true);
  }

  assert.equal(hasRealGoogleClientId("not-a-google-client"), false);
  assert.equal(shouldRenderManualLoginForm("not-a-google-client"), false);
});
