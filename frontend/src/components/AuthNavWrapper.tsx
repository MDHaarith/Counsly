"use client";

import { usePathname } from "next/navigation";

import { TabBar } from "@/components/ui/TabBar";

export function AuthNavWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const onboarding = pathname.startsWith("/onboarding");

  return (
    <>
      <main className={["mx-auto min-h-screen max-w-lg px-4", onboarding ? "pb-6" : "pb-[5.5rem]"].join(" ")}>
        {children}
      </main>
      {!onboarding && <TabBar />}
    </>
  );
}
