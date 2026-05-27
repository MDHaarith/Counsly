import Link from "next/link";
import { ArrowRight, Bookmark, FileStack, MapPin, SlidersHorizontal } from "lucide-react";

import { LoginCard } from "@/components/login-card";
import { Badge, Surface } from "@/components/ui";

const features = [
  {
    icon: FileStack,
    title: "Choice filing",
    body: "Order up to 300 college-branch rows, keep strategy notes, save snapshots, and export the exact list you file on the official portal.",
  },
  {
    icon: Bookmark,
    title: "Decision pages",
    body: "Data-ranked college explorer, branch insight with cutoff trends, and side-by-side compares without fake certainty or AI guesswork.",
  },
  {
    icon: SlidersHorizontal,
    title: "Profile-tuned workflow",
    body: "Use marks, preferred branches, district context, and official cutoff history to keep the workspace grounded in your actual constraints.",
  },
  {
    icon: MapPin,
    title: "Travel context",
    body: "Check college locations, railway context, TFC centres, and route links while comparing practical trade-offs.",
  },
];

export default function Home() {
  return (
    <div className="space-y-20 pb-16">
      {/* Top nav */}
      <nav className="flex items-center justify-between gap-4">
        <Link className="brand" href="/">
          <span className="brand-mark" />
          <span>Counsly</span>
        </Link>
        <Link className="button-secondary" href="/login">
          Sign in
        </Link>
      </nav>

      {/* Hero section */}
      <section className="relative overflow-hidden rounded-3xl border border-counsly-line bg-counsly-soft px-6 py-10 md:px-10 md:py-16">
        <div className="relative grid items-start gap-10 lg:grid-cols-[1.1fr_430px]">
          <div className="space-y-8">
            <Badge tone="coral">TNEA 2027 counselling workspace</Badge>
            <div className="space-y-4">
              <h1 className="max-w-4xl font-display text-5xl leading-[1.04] tracking-[-0.02em] text-counsly-ink md:text-7xl">
                Build a choice list you can defend.
              </h1>
              <p className="copy max-w-2xl text-lg">
                Counsly turns marks, community cutoffs, historical allotment data, shortlist order,
                and round deadlines into one calm decision surface for Tamil Nadu engineering admissions.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link className="button-primary" href="/login">
                Start your workspace <ArrowRight className="h-4 w-4" />
              </Link>
              <Link className="button-secondary" href="/explore">
                Preview college explorer
              </Link>
            </div>
            <Surface className="grid gap-4 p-5 sm:grid-cols-3" tone="soft">
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-counsly-muted">Community cutoffs</p>
                <p className="font-mono text-2xl text-counsly-ink">2020–2026</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-counsly-muted">Colleges indexed</p>
                <p className="font-mono text-2xl text-counsly-ink">500+</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-counsly-muted">Data-driven</p>
                <p className="font-mono text-2xl text-counsly-ink">No AI guesswork</p>
              </div>
            </Surface>
          </div>
          <LoginCard />
        </div>
      </section>

      {/* Features grid */}
      <section className="space-y-6">
        <div className="space-y-2">
          <Badge tone="coral">Everything you need</Badge>
          <h2 className="font-display text-4xl leading-tight text-counsly-ink md:text-5xl">
            Workspace modules at a glance
          </h2>
          <p className="copy max-w-2xl">
            From browse to compare to filing to round tracking — every decision surface is grounded in official TNEA data.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {features.map(({ body, icon: Icon, title }) => (
            <Surface className="flex items-start gap-5 p-6 transition hover:border-counsly-coral/40" key={title} tone="paper">
              <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-counsly-dark text-counsly-canvas">
                <Icon className="h-5 w-5" />
              </span>
              <div className="space-y-2">
                <h3 className="font-display text-2xl leading-tight text-counsly-ink">{title}</h3>
                <p className="text-sm leading-6 text-counsly-body">{body}</p>
              </div>
            </Surface>
          ))}
        </div>
      </section>

      {/* CTA band */}
      <Surface className="flex flex-col justify-between gap-6 p-6 md:flex-row md:items-center md:p-12" tone="coral">
        <div className="max-w-2xl space-y-3">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-white/70">Why Counsly exists</p>
          <h2 className="font-display text-4xl leading-tight text-white md:text-5xl">
            Evidence first. Certainty only when data earns it.
          </h2>
        </div>
        <div className="max-w-sm space-y-4">
          <p className="text-sm leading-6 text-white/85">
            No rank prediction. No AI counselling. No fake confidence. Just the official data, organised so you can decide with clarity.
          </p>
          <Link className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/10 px-5 py-3 text-sm font-medium text-white backdrop-blur transition hover:bg-white/20" href="/login">
            Open your workspace <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </Surface>
    </div>
  );
}
