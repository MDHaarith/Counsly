import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { OnboardingProgress } from "@/components/onboarding/OnboardingProgress";

async function isOnboardingComplete(): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get(process.env.NEXT_PUBLIC_SESSION_COOKIE_NAME ?? "counsly_session");
    if (!sessionCookie?.value) return false;

    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
    const res = await fetch(`${backendUrl}/api/profile`, {
      headers: { cookie: `${sessionCookie.name}=${sessionCookie.value}` },
    });
    if (!res.ok) return false;

    const profile = await res.json();
    // If cutoff_mark is set, onboarding is complete
    return profile?.cutoff_mark != null;
  } catch {
    return false;
  }
}

export default async function OnboardingLayout({ children }: { children: React.ReactNode }) {
  const complete = await isOnboardingComplete();
  if (complete) {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-screen py-6">
      <OnboardingProgress />
      {children}
    </div>
  );
}
