import { ProgressBar } from "@/components/ui/ProgressBar";

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen px-5 py-6">
      <div className="mb-6">
        <p className="mb-2 text-sm font-medium text-olive-gray">Counsly setup</p>
        <ProgressBar progress={33} />
      </div>
      {children}
    </div>
  );
}
