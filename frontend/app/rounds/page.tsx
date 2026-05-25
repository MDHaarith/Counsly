"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Clock3, MapPinned, ShieldCheck } from "lucide-react";

import { FeatureGate } from "@/components/feature-gate";
import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { confirmRoundDecision, fetchAiGuidance, fetchRoundStatus } from "@/lib/api.mjs";
import { confirmationOptions } from "@/lib/product";

type RoundStatus = {
  active_phase: string;
  checklist: Record<string, boolean>;
  phase?: { label: string; urgent: boolean; seconds_remaining: number };
  seconds_remaining: number;
};

function formatClock(seconds: number) {
  const safe = Math.max(0, seconds);
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;
}

export default function RoundsPage() {
  const [round, setRound] = useState<RoundStatus | null>(null);
  const [decision, setDecision] = useState("Accept and Upward");
  const [message, setMessage] = useState("Loading round status and TFC-aware guidance.");
  const [strategy, setStrategy] = useState("Data-only round guidance loads with the active phase.");

  useEffect(() => {
    Promise.all([
      fetchRoundStatus(),
      fetchAiGuidance({ community: "OC", district: "Chennai", preferred_branches: ["CS", "IT"] }),
    ])
      .then(([status, guidance]) => {
        setRound(status);
        setMessage("Live round phase loaded from the workspace API.");
        setStrategy(guidance.strategy_note);
      })
      .catch(() => {
        setRound({
          active_phase: "choice_filling",
          checklist: {
            choice_list_snapshot: false,
            official_links_checked: false,
            tfc_plan_ready: false,
            decision_confirmed: false,
          },
          phase: { label: "Choice filling window", urgent: true, seconds_remaining: 72000 },
          seconds_remaining: 72000,
        });
        setMessage("Round API unavailable. Preview tracker remains usable.");
      });
  }, []);

  const completed = useMemo(() => Object.values(round?.checklist ?? {}).filter(Boolean).length, [round]);
  const selected = confirmationOptions.find((option) => option.title === decision) || confirmationOptions[1];

  return (
    <FeatureGate>
      <div className="space-y-6">
        <PageHeader
          actions={
            <Link className="button-secondary" href="/choices">
              Open choices <ArrowRight className="h-4 w-4" />
            </Link>
          }
          description="Advanced round tracking for deadlines, confirmation consequences, TFC requirements, reporting steps, and choice-list readiness."
          eyebrow="Advanced rounds tracker"
          title="Control the round before the round controls you."
        />

        <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{message}</p>

        <div className="grid gap-3 md:grid-cols-3">
          <Metric label="Active phase" note={round?.active_phase || "preview"} value={round?.phase?.label || "Loading"} />
          <Metric label="Time left" note="Current window" value={formatClock(round?.seconds_remaining || 0)} />
          <Metric label="Checklist" note="Round readiness" value={`${completed} / 4`} />
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Surface className="space-y-5 p-6" tone="paper">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-3xl text-counsly-ink">Confirmation matrix</h2>
              <Badge tone={round?.phase?.urgent ? "coral" : "safe"}>{round?.phase?.urgent ? "Urgent" : "On track"}</Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {confirmationOptions.map((option) => (
                <button
                  className={`rounded-lg border p-4 text-left transition ${
                    decision === option.title ? "border-counsly-coral bg-counsly-card" : "border-counsly-line bg-counsly-canvas"
                  }`}
                  key={option.title}
                  onClick={() => setDecision(option.title)}
                  type="button"
                >
                  <div className="mb-2 flex items-center gap-2">
                    <Badge tone={option.tfc ? "warning" : "neutral"}>{option.tfc ? "TFC required" : "No TFC step"}</Badge>
                  </div>
                  <h3 className="font-semibold text-counsly-ink">{option.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-counsly-body">{option.consequence}</p>
                </button>
              ))}
            </div>
            <button
              className="button-primary"
              onClick={async () => {
                try {
                  const response = await confirmRoundDecision(decision);
                  setMessage(response.message);
                } catch {
                  setMessage(`${decision} selected locally. Confirmation API is not reachable.`);
                }
              }}
              type="button"
            >
              Confirm {decision}
            </button>
          </Surface>

          <div className="space-y-4">
            <Surface className="space-y-4 p-5" tone="dark">
              <Clock3 className="h-5 w-5 text-counsly-coral" />
              <h2 className="font-display text-3xl text-white">TFC-aware guidance</h2>
              <p className="text-sm leading-7 text-counsly-card">{strategy}</p>
              <p className="flex gap-2 text-sm leading-6 text-counsly-card">
                <MapPinned className="mt-1 h-4 w-4 shrink-0 text-counsly-teal" />
                {selected.tfc ? "Keep certificate and payment readiness before choosing upward movement." : "Reporting is driven by the allotted college instructions."}
              </p>
            </Surface>
            <Surface className="space-y-3 p-5" tone="soft">
              <h2 className="font-display text-3xl text-counsly-ink">Round checklist</h2>
              {[
                ["choice_list_snapshot", "Save choice snapshot"],
                ["official_links_checked", "Check official links"],
                ["tfc_plan_ready", "Prepare TFC plan"],
                ["decision_confirmed", "Confirm decision"],
              ].map(([key, label]) => (
                <p className="flex items-center gap-2 text-sm text-counsly-body" key={key}>
                  <CheckCircle2 className={`h-4 w-4 ${round?.checklist?.[key] ? "text-counsly-safe" : "text-counsly-muted"}`} />
                  {label}
                </p>
              ))}
            </Surface>
            <Surface className="space-y-3 p-5" tone="paper">
              <ShieldCheck className="h-5 w-5 text-counsly-coral" />
              <p className="text-sm leading-6 text-counsly-body">
                This page tracks only the workflow state. Always file and confirm on the official counselling portal.
              </p>
            </Surface>
          </div>
        </div>
      </div>
    </FeatureGate>
  );
}
