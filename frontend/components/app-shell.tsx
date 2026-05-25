"use client";

import Link from "next/link";
import { TimerReset } from "lucide-react";
import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { useApp } from "@/app/AppContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { broadcastBanner, logout, user } = useApp();
  const authenticated = Boolean(user && user.workspace_onboarding_step === "completed");

  useEffect(() => {
    if (authenticated && pathname !== "/dashboard" && pathname !== "/subscribe") {
      window.localStorage.setItem("counsly_last_screen", pathname);
    }
  }, [authenticated, pathname]);

  return (
    <div className="min-h-screen">
      {authenticated && broadcastBanner && (
        <div className="broadcast">
          <TimerReset className="h-4 w-4 shrink-0 text-counsly-coral" />
          <span className="truncate">{broadcastBanner}</span>
        </div>
      )}
      {authenticated && (
        <header className="desktop-shell">
          <Link className="brand" href="/dashboard">
            <span className="brand-mark" />
            <span>Counsly</span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-counsly-muted xl:inline">{user?.name}</span>
            <button className="button-quiet" onClick={logout} type="button">
              Sign out
            </button>
          </div>
        </header>
      )}
      <main className={authenticated ? "app-main-auth" : "app-main-public"}>{children}</main>
    </div>
  );
}
