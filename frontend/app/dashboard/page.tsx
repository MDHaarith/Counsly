"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, BarChart3, FileStack, GitCompareArrows, Calendar, Link2, AlertCircle, Compass, MapPin } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { fetchChoiceSnapshots, fetchChoices, fetchCompareSessions } from "@/lib/api.mjs";

type CompareSession = { createdAt: string; href: string; id: string; title: string };

const moduleLinks = [
  { href: "/recommendations", icon: Activity, label: "Recommendations", desc: "Fit-ranked college targets" },
  { href: "/choices", icon: FileStack, label: "Choice Filing", desc: "Order, snapshot, and export" },
  { href: "/compare", icon: GitCompareArrows, label: "College Compare", desc: "Side-by-side metrics" },
  { href: "/explore", icon: Compass, label: "College Explorer", desc: "Browse and search colleges" },
  { href: "/maps", icon: MapPin, label: "Travel & Maps", desc: "College travel routes & paths" },
];

export default function Dashboard() {
  const { user } = useApp();
  const [choices, setChoices] = useState<Array<{ priority: number }>>([]);
  const [snapshots, setSnapshots] = useState<Array<{ id: string }>>([]);
  const [compares, setCompares] = useState<CompareSession[]>([]);
  const [resume, setResume] = useState("/recommendations");
  const [recsViewed, setRecsViewed] = useState(false);
  const [status, setStatus] = useState("Loading workspace decision state.");

  useEffect(() => {
    setResume(window.localStorage.getItem("counsly_last_screen") || "/recommendations");
    setRecsViewed(window.localStorage.getItem("counsly_recommendations_viewed") === "true");
    
    Promise.all([
      fetchChoices(),
      fetchChoiceSnapshots(),
      fetchCompareSessions(),
    ])
      .then(([choiceRows, snapshotRows, compareRows]) => {
        setChoices(choiceRows);
        setSnapshots(snapshotRows);
        setCompares(compareRows.slice(0, 2));
        setStatus("Workspace progress loaded from choices, compares, and snapshots.");
      })
      .catch(() => setStatus("Live workspace state is not reachable. Dashboard decisions use the current browser session."));
  }, []);

  const nextAction = useMemo(() => {
    if (user && user.workspace_onboarding_step !== "completed") {
      return { href: `/onboarding/${user.workspace_onboarding_step}`, label: "Resume onboarding", title: "Complete the profile before the decision surfaces branch." };
    }
    if (!recsViewed) {
      return { href: "/recommendations", label: "View recommendations", title: "Open data-filtered recommendations before starting the filing list." };
    }
    if (!choices.length) {
      return { href: "/recommendations", label: "Start choice list", title: "Move a college-branch row into the first choice list." };
    }
    if (!snapshots.length) {
      return { href: "/choices", label: "Save snapshot", title: "Save the current choice order before the round lock." };
    }
    return { href: "/compare", label: "Compare colleges", title: "Review side-by-side college choices before finalize." };
  }, [choices.length, recsViewed, snapshots.length, user]);

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link className="button-primary" href={nextAction.href}>
            {nextAction.label} <ArrowRight className="h-4 w-4" />
          </Link>
        }
        description="One clean hub for recommendations, choices, college explorer, side-by-side compares, and news alerts."
        eyebrow="Counselling dashboard"
        title={`Welcome${user?.name ? `, ${user.name}` : ""}.`}
      />

      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{status}</p>

      {/* Next Action Surface */}
      <div className="grid gap-4">
        <Surface className="space-y-5 p-6 md:p-8" tone="soft">
          <Badge tone="coral">Next best action</Badge>
          <h2 className="max-w-3xl font-display text-4xl leading-tight text-counsly-ink">{nextAction.title}</h2>
          <div className="flex flex-wrap gap-2">
            <Link className="button-primary" href={nextAction.href}>{nextAction.label}</Link>
            <Link className="button-secondary" href={resume}>
              <ArrowRight className="h-4 w-4 rotate-180" /> Resume last screen
            </Link>
          </div>
        </Surface>
      </div>

      {/* Workspace Metric Cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Metric label="Primary list" note="Shortlist status" value={`${choices.length} rows`} />
        <Metric label="Snapshots" note="Immutable list versions" value={`${snapshots.length} saved`} />
        <Metric label="Recent compares" note="Decision sessions ready to reopen" value={`${compares.length} saved`} />
      </div>

      {/* Main Dashboard Layout Split: Left: Modules/Resume, Right: News/Alerts */}
      <div className="grid gap-6 lg:grid-cols-3">
        
        {/* Left Columns (Modules and Recent Activities) */}
        <div className="space-y-6 lg:col-span-2">
          
          {/* Module Links map */}
          <div className="space-y-4">
            <h2 className="font-display text-3xl text-counsly-ink">Workspace Modules</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {moduleLinks.map((mod) => {
                const Icon = mod.icon;
                return (
                  <Link className="surface surface-paper flex items-start gap-4 p-4 transition hover:border-counsly-coral" href={mod.href} key={mod.href}>
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-counsly-coral/10 text-counsly-coral">
                      <Icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 space-y-1">
                      <p className="text-sm font-semibold text-counsly-ink">{mod.label}</p>
                      <p className="text-xs leading-5 text-counsly-muted">{mod.desc}</p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Quick Resumes split card */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Surface className="space-y-4 p-5" tone="paper">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-display text-2xl text-counsly-ink">Shortlist Resume</h3>
                <FileStack className="h-5 w-5 text-counsly-coral" />
              </div>
              <p className="text-xs leading-5 text-counsly-muted">
                {choices.length
                  ? `${choices.length} ordered rows are ready. Snapshot before a major filing reorder.`
                  : "No primary choice rows yet. Start from a recommendation or add a branch from college explorer."}
              </p>
              <Link className="button-secondary w-full" href={choices.length ? "/choices" : "/recommendations"}>
                {choices.length ? "Open choice filing" : "Open recommendations"} <ArrowRight className="h-4 w-4" />
              </Link>
            </Surface>

            <Surface className="space-y-4 p-5" tone="paper">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-display text-2xl text-counsly-ink">Recent Compares</h3>
                <GitCompareArrows className="h-5 w-5 text-counsly-coral" />
              </div>
              {compares.length ? compares.map((session) => (
                <Link className="flex items-center justify-between gap-4 rounded-lg border border-counsly-line bg-counsly-soft p-3 text-xs text-counsly-body" href={session.href} key={session.id}>
                  <span className="truncate">{session.title}</span>
                  <ArrowRight className="h-3 w-3 shrink-0" />
                </Link>
              )) : (
                <Link className="flex items-center justify-between gap-4 rounded-lg border border-counsly-line bg-counsly-soft p-3 text-xs text-counsly-body" href="/compare">
                  <span className="truncate">Save a compare session to reopen it here.</span>
                  <ArrowRight className="h-3 w-3 shrink-0" />
                </Link>
              )}
            </Surface>
          </div>

        </div>

        {/* Right Column: PDF News / Alerts Widget */}
        <div className="space-y-6">
          <Surface className="space-y-5 p-6" tone="paper">
            <h2 className="font-display text-3xl text-counsly-ink">News & Alerts</h2>
            
            {/* 1. Important Dates */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-counsly-coral">
                <Calendar className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Important Dates</span>
              </div>
              <div className="space-y-2.5 pl-6 border-l border-counsly-line text-xs">
                <div>
                  <p className="font-medium text-counsly-ink">June 10, 2027</p>
                  <p className="text-counsly-muted">Last date for TNEA online registration and upload of certificates.</p>
                </div>
                <div>
                  <p className="font-medium text-counsly-ink">July 15 - 18, 2027</p>
                  <p className="text-counsly-muted">Choice Filing active window for Round 1 (Cutoff aggregate matches).</p>
                </div>
                <div>
                  <p className="font-medium text-counsly-ink">July 20, 2027</p>
                  <p className="text-counsly-muted">Round 1 Tentative Allotment publication.</p>
                </div>
              </div>
            </div>

            <hr className="border-counsly-line" />

            {/* 2. Official Links */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-counsly-coral">
                <Link2 className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Official Links</span>
              </div>
              <div className="grid gap-2 pl-6 text-xs font-medium">
                <a className="text-counsly-ink hover:text-counsly-coral transition flex items-center justify-between" href="https://www.tneaonline.org" target="_blank" rel="noopener noreferrer">
                  <span>TNEA Official Portal</span>
                  <ArrowRight className="h-3 w-3 -rotate-45" />
                </a>
                <a className="text-counsly-ink hover:text-counsly-coral transition flex items-center justify-between" href="https://www.annauniv.edu" target="_blank" rel="noopener noreferrer">
                  <span>Anna University Web</span>
                  <ArrowRight className="h-3 w-3 -rotate-45" />
                </a>
              </div>
            </div>

            <hr className="border-counsly-line" />

            {/* 3. Manual Updates */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-counsly-coral">
                <AlertCircle className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Manual Updates</span>
              </div>
              <div className="space-y-3 pl-6 border-l border-counsly-line text-xs text-counsly-muted">
                <div>
                  <Badge tone="coral" className="mb-1 text-[9px] px-1.5 py-0.5">Alert</Badge>
                  <p className="text-counsly-ink leading-relaxed">TNEA certificate verification scheduled at closest TFC centers. Check map view for addresses.</p>
                </div>
                <div>
                  <Badge className="mb-1 text-[9px] px-1.5 py-0.5 bg-counsly-soft text-counsly-ink">Allotment</Badge>
                  <p className="text-counsly-ink leading-relaxed">Historical community-wise cutoff aggregation updated for 2020-2026 cycles.</p>
                </div>
              </div>
            </div>

          </Surface>
        </div>

      </div>

    </div>
  );
}