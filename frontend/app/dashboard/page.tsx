"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileStack, GitCompareArrows, RotateCcw, Settings2 } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { fetchChoiceSnapshots, fetchChoices, fetchCompareSessions, fetchRoundStatus } from "@/lib/api.mjs";

type CompareSession = { createdAt: string; href: string; id: string; title: string };
type RoundPreview = { active_phase: string; checklist: Record<string, boolean>; seconds_remaining: number };

export default function Dashboard() {
  const { user } = useApp();
  const [choices, setChoices] = useState<Array<{ priority: number }>>([]);
  const [snapshots, setSnapshots] = useState<Array<{ id: string }>>([]);
  const [compares, setCompares] = useState<CompareSession[]>([]);
  const [round, setRound] = useState<RoundPreview | null>(null);
  const [resume, setResume] = useState("/recommendations");
  const [recsViewed, setRecsViewed] = useState(false);
  const [status, setStatus] = useState("Loading workspace decision state.");

  useEffect(() => {
    setResume(window.localStorage.getItem("counsly_last_screen") || "/recommendations");
    setRecsViewed(window.localStorage.getItem("counsly_recommendations_viewed") === "true");
    Promise.all([fetchChoices(), fetchChoiceSnapshots(), fetchCompareSessions(), fetchRoundStatus()])
      .then(([choiceRows, snapshotRows, compareRows, roundStatus]) => {
        setChoices(choiceRows);
        setSnapshots(snapshotRows);
        setCompares(compareRows.slice(0, 2));
        setRound(roundStatus);
        setStatus("Workspace progress loaded from choices, compares, snapshots, and round state.");
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
    return { href: "/rounds", label: "Review round actions", title: "Check the next active round consequence before filing changes." };
  }, [choices.length, recsViewed, snapshots.length, user]);

  const completedRoundSteps = Object.values(round?.checklist ?? {}).filter(Boolean).length;

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link className="button-primary" href={nextAction.href}>
            {nextAction.label} <ArrowRight className="h-4 w-4" />
          </Link>
        }
        description="One clean hub for recommendations, choices, college details, compares, analytics, and round decisions."
        eyebrow="Counselling dashboard"
        title={`Welcome${user?.name ? `, ${user.name}` : ""}.`}
      />

      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{status}</p>

      <div className="grid gap-4">
        <Surface className="space-y-5 p-6 md:p-8" tone="soft">
          <Badge tone="coral">Next best action</Badge>
          <h2 className="max-w-3xl font-display text-4xl leading-tight text-counsly-ink">{nextAction.title}</h2>
          <div className="flex flex-wrap gap-2">
            <Link className="button-primary" href={nextAction.href}>{nextAction.label}</Link>
            <Link className="button-secondary" href={resume}>
              <RotateCcw className="h-4 w-4" /> Resume last screen
            </Link>
            <Link className="button-secondary" href="/admin">
              <Settings2 className="h-4 w-4" /> Operations
            </Link>
          </div>
        </Surface>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Primary list" note="Shortlist status" value={`${choices.length} rows`} />
        <Metric label="Snapshots" note="Immutable list versions" value={`${snapshots.length} saved`} />
        <Metric label="Recent compares" note="Decision sessions ready to reopen" value={`${compares.length} saved`} />
        <Metric label="Round tasks" note="Checklist progress" value={`${completedRoundSteps} / 4`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Surface className="space-y-4 p-6" tone="paper">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display text-3xl text-counsly-ink">Shortlist resume</h2>
            <FileStack className="h-5 w-5 text-counsly-coral" />
          </div>
          <p className="text-sm leading-6 text-counsly-body">
            {choices.length
              ? `${choices.length} ordered rows are ready. Snapshot before a major filing reorder.`
              : "No primary choice rows yet. Start from a recommendation or add a branch from college insight."}
          </p>
          <Link className="button-secondary" href={choices.length ? "/choices" : "/recommendations"}>
            {choices.length ? "Open choice filing" : "Open recommendations"} <ArrowRight className="h-4 w-4" />
          </Link>
        </Surface>

        <Surface className="space-y-4 p-6" tone="paper">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display text-3xl text-counsly-ink">Recent compares</h2>
            <GitCompareArrows className="h-5 w-5 text-counsly-coral" />
          </div>
          {compares.length ? compares.map((session) => (
            <Link className="flex items-center justify-between gap-4 rounded-lg border border-counsly-line bg-counsly-soft p-4 text-sm text-counsly-body" href={session.href} key={session.id}>
              <span>{session.title}</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          )) : (
            <Link className="flex items-center justify-between gap-4 rounded-lg border border-counsly-line bg-counsly-soft p-4 text-sm text-counsly-body" href="/compare">
              <span>Save a compare session to reopen it here.</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}
        </Surface>
      </div>
    </div>
  );
}
