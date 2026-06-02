import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";

import ts from "typescript";

const repoRoot = path.resolve(import.meta.dirname, "..");
const storedUserKey = "counsly_user";

class MemoryStorage {
  #items = new Map();

  getItem(key) {
    return this.#items.has(key) ? this.#items.get(key) : null;
  }

  setItem(key, value) {
    this.#items.set(key, String(value));
  }

  removeItem(key) {
    this.#items.delete(key);
  }
}

function loadAppContext(windowStub) {
  const source = fs.readFileSync(path.join(repoRoot, "app", "AppContext.tsx"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      jsx: ts.JsxEmit.React,
      module: ts.ModuleKind.CommonJS,
    },
  }).outputText;

  const module = { exports: {} };
  const reactMock = {
    createContext(defaultValue) {
      return { defaultValue, Provider: "Provider" };
    },
    createElement(type, props, children) {
      return { children, props, type };
    },
    useContext(context) {
      return context.defaultValue;
    },
    useEffect(callback) {
      callback();
    },
    useState(initialValue) {
      return [initialValue, () => {}];
    },
  };

  const requireMock = (specifier) => {
    if (specifier === "react") return reactMock;
    if (specifier === "@/lib/api.mjs") {
      return {
        API_BASE_URL: "http://api.test",
        clearStoredToken() {},
        startSession() {},
      };
    }
    if (specifier === "@/lib/device-fingerprint.mjs") {
      return { createDeviceFingerprint: async () => "fingerprint" };
    }
    if (specifier === "@/lib/error-logging.mjs") {
      return { installClientErrorHandlers() {} };
    }
    throw new Error(`Unexpected module import: ${specifier}`);
  };

  vm.runInNewContext(compiled, {
    exports: module.exports,
    module,
    require: requireMock,
    window: windowStub,
  });

  return module.exports;
}

test("AppProvider clears invalid stored user JSON without throwing", () => {
  const windowStub = {
    localStorage: new MemoryStorage(),
    sessionStorage: new MemoryStorage(),
  };
  windowStub.sessionStorage.setItem(storedUserKey, "{invalid session json");
  windowStub.localStorage.setItem(storedUserKey, "{invalid local json");

  const { AppProvider } = loadAppContext(windowStub);

  assert.doesNotThrow(() => AppProvider({ children: "child" }));
  assert.equal(windowStub.sessionStorage.getItem(storedUserKey), null);
  assert.equal(windowStub.localStorage.getItem(storedUserKey), null);
});
