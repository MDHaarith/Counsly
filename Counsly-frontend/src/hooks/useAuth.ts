"use client";

import { useEffect, useState } from "react";

import { getSession } from "@/lib/api";

export interface SessionUser {
  app_user_id: string;
  workspace_id: string;
  email: string;
  display_name: string | null;
  paid: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getSession<SessionUser>()
      .then((session) => {
        if (!active) return;
        setUser(session);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setUser(null);
        setError(err instanceof Error ? err.message : "Not authenticated");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return { user, loading, error, authenticated: Boolean(user) };
}
