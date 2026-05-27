"use client";

import Link from "next/link";
import { TimerReset, Home, Sparkles, FileStack, Compass, LogOut } from "lucide-react";
import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { useApp } from "@/app/AppContext";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { broadcastBanner, logout, user } = useApp();
  const authenticated = Boolean(user && user.workspace_onboarding_step === "completed");

  useEffect(() => {
    if (authenticated && pathname !== "/dashboard") {
      window.localStorage.setItem("counsly_last_screen", pathname);
    }
  }, [authenticated, pathname]);

  const coreNavItems = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/recommendations", label: "Recommendations" },
    { href: "/choices", label: "Choice Filing" },
    { href: "/compare", label: "College Compare" },
    { href: "/explore", label: "College Explorer" },
    { href: "/maps", label: "Travel & Maps" },
  ];

  return (
    <div className="min-h-screen bg-counsly-canvas">
      {authenticated && broadcastBanner && (
        <div className="broadcast flex items-center justify-center">
          <TimerReset className="h-4 w-4 shrink-0 text-counsly-coral" />
          <span className="truncate font-medium">{broadcastBanner}</span>
        </div>
      )}
      
      {authenticated && (
        <>
          {/* Desktop Shell Navigation */}
          <header className="desktop-shell sticky top-4 z-40 mx-auto mt-4 hidden w-[calc(100%-2rem)] max-w-7xl items-center justify-between gap-5 rounded-2xl border border-counsly-line bg-counsly-canvas/95 px-5 py-3 shadow-[0_14px_40px_rgba(20,20,19,0.08)] backdrop-blur md:flex">
            <Link className="brand" href="/dashboard">
              <span className="brand-mark" />
              <span className="font-semibold tracking-tight">Counsly</span>
            </Link>
            
            {/* Desktop Navigation Links */}
            <nav className="flex items-center gap-1.5">
              {coreNavItems.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`nav-link px-3 py-2 text-sm font-medium transition-colors ${
                      isActive 
                        ? "nav-link-active bg-counsly-soft text-counsly-ink" 
                        : "text-counsly-muted hover:text-counsly-ink hover:bg-counsly-soft/50"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center gap-4">
              <span className="hidden text-sm font-medium text-counsly-muted xl:inline">{user?.name}</span>
              <button 
                className="button-secondary min-h-9 px-3 py-1.5 text-xs font-semibold flex items-center gap-1.5 hover:bg-counsly-soft transition" 
                onClick={logout} 
                type="button"
              >
                <LogOut className="h-3.5 w-3.5" /> Sign out
              </button>
            </div>
          </header>

          {/* Mobile Shell Bottom Navigation */}
          <nav className="mobile-shell fixed bottom-3 left-3 right-3 z-40 grid grid-cols-4 gap-1 rounded-2xl border border-counsly-line bg-counsly-canvas/95 p-2 shadow-[0_18px_45px_rgba(20,20,19,0.15)] backdrop-blur md:hidden">
            <Link 
              href="/dashboard" 
              className={`mobile-nav-link flex flex-col items-center justify-center py-1 text-center rounded-xl transition ${
                pathname === "/dashboard" ? "mobile-nav-link-active bg-counsly-soft text-counsly-ink" : "text-counsly-muted"
              }`}
            >
              <Home className="h-5 w-5" />
              <span className="text-[10px] font-medium mt-1">Home</span>
            </Link>
            <Link 
              href="/recommendations" 
              className={`mobile-nav-link flex flex-col items-center justify-center py-1 text-center rounded-xl transition ${
                pathname === "/recommendations" ? "mobile-nav-link-active bg-counsly-soft text-counsly-ink" : "text-counsly-muted"
              }`}
            >
              <Sparkles className="h-5 w-5" />
              <span className="text-[10px] font-medium mt-1">Recs</span>
            </Link>
            <Link 
              href="/choices" 
              className={`mobile-nav-link flex flex-col items-center justify-center py-1 text-center rounded-xl transition ${
                pathname === "/choices" ? "mobile-nav-link-active bg-counsly-soft text-counsly-ink" : "text-counsly-muted"
              }`}
            >
              <FileStack className="h-5 w-5" />
              <span className="text-[10px] font-medium mt-1">Choices</span>
            </Link>
            <Link 
              href="/explore" 
              className={`mobile-nav-link flex flex-col items-center justify-center py-1 text-center rounded-xl transition ${
                pathname === "/explore" || pathname.startsWith("/explore/") ? "mobile-nav-link-active bg-counsly-soft text-counsly-ink" : "text-counsly-muted"
              }`}
            >
              <Compass className="h-5 w-5" />
              <span className="text-[10px] font-medium mt-1">Explore</span>
            </Link>
          </nav>
        </>
      )}

      <main className={authenticated ? "app-main-auth" : "app-main-public"}>{children}</main>
    </div>
  );
}
