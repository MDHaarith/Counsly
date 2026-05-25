"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useApp } from "@/app/AppContext";
import { paidFeatureDestination } from "@/lib/access.mjs";

export function FeatureGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useApp();
  const destination = paidFeatureDestination(pathname);
  const locked = Boolean(destination && user && !user.subscription_active);

  useEffect(() => {
    if (locked) router.replace(destination);
  }, [destination, locked, router]);

  if (locked) {
    return <p className="rounded-xl border border-counsly-line bg-counsly-canvas p-4 text-sm text-counsly-body">Opening the Full Access paywall...</p>;
  }

  return children;
}
