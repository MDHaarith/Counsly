"use client";

import Link from "next/link";

import { useApp } from "@/app/AppContext";
import { FeatureGate } from "@/components/feature-gate";
import { Badge, Metric, PageHeader, PremiumBoard, Surface } from "@/components/ui";
import { trendRows } from "@/lib/product";

export default function AnalyticsPage() {
  const { user } = useApp();

  return (
    <FeatureGate>
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link className="button-secondary" href="/explore">
            Open explorer
          </Link>
        }
        description="Cutoff movement, seat signals, and safety margins for the branch decisions already in your workspace."
        eyebrow="Trend analytics"
        title="Read the pressure behind each cutoff."
      />

      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="Community" note="Current profile filter" value="OC" />
        <Metric label="Trend span" note="Historical cutoffs available" value="2023-2026" />
        <Metric label="Safety margin" note="PSG IT against current cutoff" value="+1.50" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_380px]">
        <Surface className="space-y-4 p-6" tone="paper">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 className="font-display text-3xl text-counsly-ink">Cutoff bands</h2>
            <div className="flex flex-wrap gap-2">
              <Badge tone="safe">Safe</Badge>
              <Badge tone="warning">Moderate</Badge>
              <Badge tone="coral">Ambitious</Badge>
            </div>
          </div>
          <div className="space-y-3">
            {trendRows.map((row) => (
              <div className="grid gap-3 rounded-lg border border-counsly-line p-3 sm:grid-cols-[72px_1fr]" key={row.year}>
                <p className="font-mono text-sm text-counsly-muted">{row.year}</p>
                <div className="grid gap-2 sm:grid-cols-3">
                  <span className="rounded-md bg-counsly-safe/15 px-3 py-2 font-mono text-sm text-counsly-ink">{row.safe}</span>
                  <span className="rounded-md bg-counsly-gold/25 px-3 py-2 font-mono text-sm text-counsly-ink">{row.moderate}</span>
                  <span className="rounded-md bg-counsly-coral/15 px-3 py-2 font-mono text-sm text-counsly-ink">{row.ambitious}</span>
                </div>
              </div>
            ))}
          </div>
        </Surface>

        <Surface className="space-y-4 p-6" tone="dark">
          <Badge tone="dark">Decision note</Badge>
          <h2 className="font-display text-3xl text-white">Why safety margins matter</h2>
          <p className="text-sm leading-6 text-counsly-card">
            A cutoff near the student band should stay labelled ambitious until newer allotment evidence tightens it.
          </p>
          {!user?.subscription_active && (
            <PremiumBoard
              body="Placement rows, detailed branch charts, and longer trend history require Full Access."
              title="Premium trend context"
            />
          )}
        </Surface>
      </div>
    </div>
    </FeatureGate>
  );
}
