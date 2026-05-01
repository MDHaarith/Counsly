import { OnboardingProgress } from "@/components/onboarding/OnboardingProgress";

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen px-5 py-6">
      <OnboardingProgress />
      {children}
    </div>
  );
}
