"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";

import { useApp } from "@/app/AppContext";
import { Surface } from "@/components/ui";
import { hasRealGoogleClientId, shouldRenderManualLoginForm } from "@/lib/auth-config.mjs";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
const hasRealGoogleClient = hasRealGoogleClientId(GOOGLE_CLIENT_ID);
const showManualLoginForm = shouldRenderManualLoginForm(GOOGLE_CLIENT_ID);

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

  useEffect(() => {
    if (!hasRealGoogleClient || !googleButtonRef.current || !window.google?.accounts?.id) {
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
  }, [email, login, name, router]);

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
    <Surface className={`relative overflow-hidden ${compact ? "p-5" : "p-6 md:p-8"}`} tone="paper">
      {/* Subtle radial gradient decoration */}
      <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-counsly-coral/5 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-counsly-teal/5 blur-3xl" />

      <div className="relative space-y-5">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-counsly-dark text-counsly-canvas">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-counsly-muted">Student workspace</p>
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="font-display text-3xl leading-tight text-counsly-ink">Continue your counselling workspace</h2>
          <p className="text-sm leading-6 text-counsly-muted">
            {hasRealGoogleClient
              ? "Use Google sign-in to pick up your shortlists, snapshots, and compare sessions — no password needed."
              : showManualLoginForm
                ? "Manual name/email login is development-only. Enter any name and email here only when the Google client ID is missing or set to a dev/mock value."
                : "Google sign-in is required, but the configured Google client ID is not valid. Contact support before continuing."}
          </p>
        </div>

        {hasRealGoogleClient ? (
          <div className="space-y-3">
            <div className="flex justify-center" ref={googleButtonRef} />
            <p className="text-center text-xs leading-5 text-counsly-muted">
              Production access uses Google identity verification before opening your workspace.
            </p>
          </div>
        ) : showManualLoginForm ? (
          <>
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-3">
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
              </div>

              <button className="button-primary w-full" disabled={busy} type="submit">
                {busy ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Opening workspace...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Continue to dashboard <ArrowRight className="h-4 w-4" />
                  </span>
                )}
              </button>
            </form>

            <div className="rounded-lg border border-counsly-line bg-counsly-soft/50 px-4 py-3">
              <p className="text-xs leading-5 text-counsly-muted">
                <span className="font-medium text-counsly-ink">Dev mode only:</span> Manual login is available only for local development or mock Google-client setups. Production uses Google sign-in as the primary authentication action.
              </p>
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
            <p className="text-sm text-red-600">
              Authentication is unavailable because the Google client ID is neither empty nor a recognized development/mock value nor a real Google OAuth client ID.
            </p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex items-center gap-2.5 rounded-lg border border-counsly-line bg-counsly-soft/30 px-4 py-3">
          <ShieldCheck className="h-4 w-4 shrink-0 text-counsly-safe" />
          <p className="text-xs leading-5 text-counsly-muted">
            Private per-user choice lists, compare sessions, and filing notes — isolated by workspace.
          </p>
        </div>
      </div>
    </Surface>
  );
}
