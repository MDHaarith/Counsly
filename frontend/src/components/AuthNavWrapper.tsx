"use client";

import { usePathname } from "next/navigation";

import { TabBar } from "@/components/ui/TabBar";

export function AuthNavWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const onboarding = pathname.startsWith("/onboarding");

  return (
    <>
      <main className={["mx-auto min-h-screen max-w-md", onboarding ? "pb-6" : "pb-24"].join(" ")}>
        {children}
      </main>
      {!onboarding && <TabBar />}
    </>
  );
}
