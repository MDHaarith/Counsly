"use client";

import type React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useApp } from "@/app/AppContext";
import { Surface } from "@/components/ui";

function redirectTarget(user: ReturnType<typeof useApp>["user"]) {
  if (!user) return "/login";
  if (user.workspace_onboarding_step !== "completed") return "/onboarding";
  return null;
}

export function FeatureGate({ children }: { children: React.ReactNode }) {
  const { user, userHydrated } = useApp();
  const pathname = usePathname();
  const router = useRouter();
  const target = userHydrated ? redirectTarget(user) : null;

  useEffect(() => {
    if (target && pathname !== target) {
      router.replace(target);
    }
  }, [pathname, router, target]);

  if (!userHydrated) {
    return (
      <Surface className="space-y-3 p-6" tone="paper">
        <p className="eyebrow">Checking workspace access</p>
        <h1 className="font-display text-3xl text-counsly-ink">Preparing your Counsly workspace...</h1>
        <p className="text-sm leading-6 text-counsly-body">We are confirming your session before opening this protected surface.</p>
      </Surface>
    );
  }

  if (target) {
    const onboardingBlocked = Boolean(user);
    return (
      <Surface className="space-y-4 p-6" tone="paper">
        <p className="eyebrow">Protected workspace</p>
        <h1 className="font-display text-3xl text-counsly-ink">
          {onboardingBlocked ? "Complete onboarding to continue." : "Sign in to continue."}
        </h1>
        <p className="text-sm leading-6 text-counsly-body">
          {onboardingBlocked
            ? "This page is available after your workspace onboarding is marked completed. Backend authorization remains the source of truth for all protected data."
            : "This page belongs to a signed-in Counsly workspace. Backend authorization remains the source of truth for all protected data."}
        </p>
        <Link className="button-primary w-fit" href={target}>
          {onboardingBlocked ? "Go to onboarding" : "Go to login"}
        </Link>
      </Surface>
    );
  }

  return children;
}
