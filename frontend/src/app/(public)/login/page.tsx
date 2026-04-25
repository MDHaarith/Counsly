"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiClient } from "@/lib/api";

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function startGoogle() {
    setLoading(true);
    setError(null);
    try {
      const payload = await apiClient<{ url: string }>("/api/auth/google/start");
      window.location.href = payload.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google login is not ready yet.");
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-8">
      <div className="space-y-6">
        <div>
          <p className="text-sm font-medium text-olive-gray">Counsly account</p>
          <h1 className="mt-2 font-serif text-[34px] font-medium leading-tight">Continue with Google</h1>
          <p className="mt-3 text-sm leading-relaxed text-olive-gray">Your workspace keeps marks, choices, and payment access together for this counselling season.</p>
        </div>
        <Card>
          <Button onClick={startGoogle} disabled={loading}>{loading ? "Opening Google..." : "Continue with Google"}</Button>
          {error && <p className="mt-3 text-sm text-error-crimson">{error}</p>}
          <p className="mt-4 text-xs leading-relaxed text-stone-gray">No password. Counsly stores your Google ID only as an identity reference.</p>
        </Card>
      </div>
    </main>
  );
}
