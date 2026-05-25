import Link from "next/link";
import { ArrowRight, FileStack, Radar, ShieldCheck, TimerReset } from "lucide-react";

import { LoginCard } from "@/components/login-card";
import { Badge, Surface } from "@/components/ui";

const surfaces = [
  {
    icon: FileStack,
    title: "Choice filing",
    body: "Order up to 300 college-branch rows, keep strategy notes, save snapshots, and export the exact list you file.",
  },
  {
    icon: Radar,
    title: "Decision pages",
    body: "Use data-ranked explore, college insight, and comparisons without fake certainty.",
  },
  {
    icon: TimerReset,
    title: "Round control",
    body: "See deadlines, confirmation consequences, TFC steps, and reporting checklists before the lock window.",
  },
];

export default function Home() {
  return (
    <div className="space-y-16 pb-10">
      <nav className="flex items-center justify-between gap-4">
        <Link className="brand" href="/">
          <span className="brand-mark" />
          <span>Counsly</span>
        </Link>
        <Link className="button-secondary" href="/login">
          Login
        </Link>
      </nav>

      <section className="grid items-start gap-8 lg:grid-cols-[minmax(0,1.1fr)_430px]">
        <div className="space-y-8 pt-4">
          <Badge tone="coral">TNEA 2027 counselling workspace</Badge>
          <div className="space-y-5">
            <h1 className="display-title max-w-4xl">
              Build a choice list you can defend when counselling gets real.
            </h1>
            <p className="copy max-w-2xl text-lg">
              Counsly turns marks, community cutoffs, shortlist order, and round deadlines into one
              calm decision surface for Tamil Nadu engineering admissions.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className="button-primary" href="/login">
              Start with marks <ArrowRight className="h-4 w-4" />
            </Link>
            <Link className="button-secondary" href="/explore">
              Preview college explorer
            </Link>
          </div>
          <Surface className="grid gap-4 p-5 sm:grid-cols-3" tone="dark">
            <div className="space-y-1">
              <p className="eyebrow text-counsly-card">Student cutoff</p>
              <p className="font-mono text-2xl text-white">196.50</p>
            </div>
            <div className="space-y-1">
              <p className="eyebrow text-counsly-card">Choice status</p>
              <p className="font-mono text-2xl text-white">18 saved</p>
            </div>
            <div className="space-y-1">
              <p className="eyebrow text-counsly-card">Round clock</p>
              <p className="font-mono text-2xl text-white">01:14:22</p>
            </div>
          </Surface>
        </div>
        <LoginCard />
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {surfaces.map(({ body, icon: Icon, title }) => (
          <Surface className="space-y-4 p-6" key={title} tone="soft">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-counsly-dark text-counsly-canvas">
              <Icon className="h-5 w-5" />
            </span>
            <div className="space-y-2">
              <h2 className="font-display text-3xl text-counsly-ink">{title}</h2>
              <p className="text-sm leading-6 text-counsly-body">{body}</p>
            </div>
          </Surface>
        ))}
      </section>

      <Surface className="flex flex-col justify-between gap-6 p-6 md:flex-row md:items-center md:p-10" tone="coral">
        <div className="max-w-2xl space-y-2">
          <p className="eyebrow text-white/80">Trust rule</p>
          <h2 className="font-display text-4xl text-white">Evidence first. Precision only when data earns it.</h2>
        </div>
        <p className="flex max-w-sm items-start gap-2 text-sm leading-6 text-white/90">
          <ShieldCheck className="mt-1 h-4 w-4 shrink-0" />
          Recommendations stay data-only and eligibility-gated; no fake certainty.
        </p>
      </Surface>
    </div>
  );
}
