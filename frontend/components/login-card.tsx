"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";

import { useApp } from "@/app/AppContext";
import { Badge, Surface } from "@/components/ui";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (options: Record<string, unknown>) => void;
          renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

export function LoginCard({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const { login } = useApp();
  const googleButtonRef = useRef<HTMLDivElement | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const showGoogleSignIn = Boolean(GOOGLE_CLIENT_ID);

  useEffect(() => {
    if (!showGoogleSignIn || !googleButtonRef.current || !window.google?.accounts?.id) {
      return;
    }

    window.google.accounts.id.initialize({
      callback: async (response: { credential?: string }) => {
        if (!response.credential) {
          setError("Google sign-in did not return a valid credential.");
          return;
        }
        setBusy(true);
        setError("");
        try {
          const profile = await login(email, name, response.credential);
          router.push(profile.workspace_onboarding_step === "completed" ? "/dashboard" : "/onboarding");
        } catch (err) {
          setError(err instanceof Error ? err.message : "Unable to open your workspace right now.");
        } finally {
          setBusy(false);
        }
      },
      client_id: GOOGLE_CLIENT_ID,
    });

    googleButtonRef.current.innerHTML = "";
    window.google.accounts.id.renderButton(googleButtonRef.current, {
      size: "large",
      text: "continue_with",
      theme: "outline",
      width: 320,
    });
  }, [email, login, name, router, showGoogleSignIn]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!name || !email) return;
    setBusy(true);
    setError("");
    try {
      const profile = await login(email, name);
      router.push(profile.workspace_onboarding_step === "completed" ? "/dashboard" : "/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to open your workspace right now.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Surface className={`space-y-5 ${compact ? "p-5" : "p-6 md:p-8"}`} tone="paper">
      <Badge tone="coral">Student workspace</Badge>
      <div className="space-y-2">
        <h2 className="font-display text-3xl text-counsly-ink">Open your Counsly file.</h2>
        <p className="text-sm leading-6 text-counsly-muted">
          Start with your marks, community, and preferred branches. Production access uses a live backend session with Google identity verification.
        </p>
      </div>
      <form className="space-y-3" onSubmit={submit}>
        <label className="field-label">
          Full name
          <input
            className="field"
            onChange={(event) => setName(event.target.value)}
            placeholder="Mohamed Haarith"
            required
            value={name}
          />
        </label>
        <label className="field-label">
          Google email
          <input
            className="field"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="student@gmail.com"
            required
            type="email"
            value={email}
          />
        </label>
        <button className="button-primary w-full" disabled={busy || showGoogleSignIn} type="submit">
          {showGoogleSignIn ? "Use Google sign-in below" : busy ? "Opening workspace..." : "Continue to eligibility"} <ArrowRight className="h-4 w-4" />
        </button>
      </form>
      {GOOGLE_CLIENT_ID ? (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.2em] text-counsly-muted">Recommended for production</p>
          <div ref={googleButtonRef} />
        </div>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <p className="flex items-center gap-2 text-xs leading-5 text-counsly-muted">
        <ShieldCheck className="h-4 w-4 text-counsly-safe" />
        Private per-user choice lists, compare sessions, and filing notes.
      </p>
    </Surface>
  );
}
