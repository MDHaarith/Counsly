"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";

const steps = ["/onboarding/marks", "/onboarding/details", "/onboarding/rank"];

export function OnboardingProgress() {
  const pathname = usePathname();
  const index = Math.max(0, steps.findIndex((step) => pathname.startsWith(step)));
  const progress = ((index + 1) / steps.length) * 100;
  const previous = index > 0 ? steps[index - 1] : "/dashboard";

  return (
    <div className="mb-6">
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-olive-gray">Counsly setup</p>
        <Link href={previous}>
          <Button variant="ghost" className="h-10 w-auto px-3">
            Back
          </Button>
        </Link>
      </div>
      <ProgressBar progress={progress} />
    </div>
  );
}
