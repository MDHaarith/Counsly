import Link from "next/link";

import { LoginCard } from "@/components/login-card";

export default function LoginPage() {
  return (
    <div className="grid min-h-[calc(100vh-6rem)] items-center gap-12 lg:grid-cols-[1fr_440px]">
      <div className="hidden space-y-6 lg:block">
        <Link className="brand" href="/">
          <span className="brand-mark" />
          <span>Counsly</span>
        </Link>
        <div className="space-y-3">
          <h1 className="font-display text-6xl leading-[1.04] tracking-[-0.02em] text-counsly-ink">
            Welcome back to your counselling workspace.
          </h1>
          <p className="max-w-xl text-base leading-7 text-counsly-body">
            Your workspace carries every compare session, snapshot, and filing note. Sign in with your Google email to pick up exactly where you left off.
          </p>
        </div>
        <div className="grid gap-3 rounded-2xl border border-counsly-line bg-counsly-soft/60 p-5">
          <p className="flex gap-3 text-sm leading-6 text-counsly-body">
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-counsly-coral/10 text-xs font-bold text-counsly-coral">1</span>
            Recommendations ranked by fit score — filtered by district, branch, and cutoff
          </p>
          <p className="flex gap-3 text-sm leading-6 text-counsly-body">
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-counsly-coral/10 text-xs font-bold text-counsly-coral">2</span>
            Side-by-side college compare with fees, cutoffs, placement, and transport rows
          </p>
          <p className="flex gap-3 text-sm leading-6 text-counsly-body">
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-counsly-coral/10 text-xs font-bold text-counsly-coral">3</span>
            Round tracker with confirmation options, TFC guidance, and deadline clock
          </p>
        </div>
      </div>
      <LoginCard compact />
    </div>
  );
}