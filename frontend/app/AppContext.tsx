"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

import { API_BASE_URL, clearStoredToken, startSession } from "@/lib/api.mjs";
import { createDeviceFingerprint } from "@/lib/device-fingerprint.mjs";
import { installClientErrorHandlers } from "@/lib/error-logging.mjs";

export interface UserProfile {
  id: string;
  name: string;
  google_email: string;
  subscription_active: boolean;
  subscription_expiry?: string;
  welcome_message_sent: boolean;
  roll_number?: string;
  roll_number_verified: boolean;
  workspace_onboarding_step: string;
}

export interface PhaseContextType {
  broadcastBanner: string;
  user: UserProfile | null;
  login: (email: string, name: string, googleIdToken?: string) => Promise<UserProfile>;
  logout: () => void;
  refreshUser: () => void;
  setSubscriptionActive: (active: boolean) => void;
  setWorkspaceOnboardingStep: (step: string) => void;
}

const AppContext = createContext<PhaseContextType | undefined>(undefined);
const STORED_USER_KEY = "counsly_user";

function readStoredUser() {
  if (typeof window === "undefined") return null;

  const sessionValue = window.sessionStorage?.getItem(STORED_USER_KEY);
  if (sessionValue) return JSON.parse(sessionValue);

  const legacyValue = window.localStorage?.getItem(STORED_USER_KEY);
  if (!legacyValue) return null;

  window.sessionStorage?.setItem(STORED_USER_KEY, legacyValue);
  window.localStorage?.removeItem(STORED_USER_KEY);
  return JSON.parse(legacyValue);
}

function writeStoredUser(profile: UserProfile) {
  if (typeof window === "undefined") return;
  const serialized = JSON.stringify(profile);
  window.sessionStorage?.setItem(STORED_USER_KEY, serialized);
  window.localStorage?.removeItem(STORED_USER_KEY);
}

function clearStoredUser() {
  if (typeof window === "undefined") return;
  window.sessionStorage?.removeItem(STORED_USER_KEY);
  window.localStorage?.removeItem(STORED_USER_KEY);
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used within an AppProvider");
  return context;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [broadcastBanner, setBroadcastBanner] = useState("Round 1 choice filing is currently active. Review choices, compare targets, and check the round tracker before locking decisions.");
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    const savedUser = readStoredUser();
    if (savedUser) {
      setUser(savedUser);
    }
  }, []);

  useEffect(() => {
    installClientErrorHandlers({ baseUrl: API_BASE_URL, userId: user?.id });
  }, [user?.id]);

  const login = async (email: string, name: string, googleIdToken?: string) => {
    const deviceFingerprint = await createDeviceFingerprint();
    const session = await startSession({
      device_fingerprint_hash: deviceFingerprint || undefined,
      google_email: email,
      google_id_token: googleIdToken,
      name,
    });
    setUser(session.profile);
    writeStoredUser(session.profile);
    return session.profile;
  };

  const logout = () => {
    setUser(null);
    clearStoredUser();
    clearStoredToken();
  };

  const refreshUser = () => {
    if (user) {
      writeStoredUser(user);
    }
  };

  const setSubscriptionActive = (active: boolean) => {
    if (user) {
      const updated = { ...user, subscription_active: active };
      setUser(updated);
      writeStoredUser(updated);
    }
  };

  const setWorkspaceOnboardingStep = (step: string) => {
    if (user) {
      const updated = { ...user, workspace_onboarding_step: step };
      setUser(updated);
      writeStoredUser(updated);
    }
  };

  return (
    <AppContext.Provider value={{
      broadcastBanner,
      user,
      login,
      logout,
      refreshUser,
      setSubscriptionActive,
      setWorkspaceOnboardingStep
    }}>
      {children}
    </AppContext.Provider>
  );
}
