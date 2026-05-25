"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Banknote,
  Building2,
  DollarSign,
  GraduationCap,
  TrendingUp,
} from "lucide-react";

import { FeatureGate } from "@/components/feature-gate";
import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { fetchFinancialMetrics, fetchRevenue } from "@/lib/api.mjs";

type FinancialMetrics = {
  total_projected_revenue?: number;
  average_fee?: number;
  affordable_colleges?: number;
  premium_colleges?: number;
};

type RevenueBreakdown = {
  college_type?: string;
  total_fees?: number;
  college_count?: number;
  avg_fee?: number;
};

type AffordabilityTier = {
  tier?: string;
  college_count?: number;
  min_fee?: number;
  max_fee?: number;
  avg_fee?: number;
};

type RoiScore = {
  college_code?: string;
  college_name?: string;
  avg_fee?: number;
  avg_package?: number;
  roi_score?: number;
  tier?: string;
};

type RevenueData = {
  breakdown?: RevenueBreakdown[];
  affordability_tiers?: AffordabilityTier[];
  roi_table?: RoiScore[];
};

export default function FinancialsPage() {
  const [metrics, setMetrics] = useState<FinancialMetrics | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [m, r] = await Promise.all([fetchFinancialMetrics(), fetchRevenue()]);
      setMetrics(m);
      setRevenueData(r);
    } catch {
      setError("Financial data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatCurrency = (val: number | undefined | null) => {
    if (val == null) return "—";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const metricCards = [
    {
      label: "Total Projected Revenue",
      value: formatCurrency(metrics?.total_projected_revenue),
      icon: DollarSign,
      note: "Annual projected",
    },
    {
      label: "Average Fee",
      value: formatCurrency(metrics?.average_fee),
      icon: Banknote,
      note: "Across all colleges",
    },
    {
      label: "Affordable Colleges",
      value: String(metrics?.affordable_colleges ?? "—"),
      icon: GraduationCap,
      note: "Below avg. fee threshold",
    },
    {
      label: "Premium Colleges",
      value: String(metrics?.premium_colleges ?? "—"),
      icon: Building2,
      note: "Above avg. fee threshold",
    },
  ];

  return (
    <FeatureGate>
      <div className="space-y-6">
        <PageHeader
          description="Revenue projections, fee breakdowns, affordability tiers, and ROI scores across all colleges."
          eyebrow="Financial Analytics"
          title="Understanding the cost landscape."
        />

        {loading && (
          <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
            Loading financial data...
          </p>
        )}

        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Metric cards */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {metricCards.map((item) => (
                <Surface className="space-y-2 p-4" key={item.label} tone="paper">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-4 w-4 text-counsly-coral" />
                    <p className="eyebrow">{item.label}</p>
                  </div>
                  <p className="font-mono text-2xl font-semibold text-counsly-ink">{item.value}</p>
                  {item.note && <p className="text-xs text-counsly-muted">{item.note}</p>}
                </Surface>
              ))}
            </div>

            {/* Revenue breakdown by college type */}
            <Surface className="space-y-4 p-5" tone="soft">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-counsly-coral" />
                <h2 className="font-display text-2xl text-counsly-ink">Revenue breakdown by college type</h2>
              </div>
              {revenueData?.breakdown?.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-counsly-line">
                        <th className="px-3 py-2 font-medium text-counsly-muted">College Type</th>
                        <th className="px-3 py-2 font-medium text-counsly-muted">Total Fees</th>
                        <th className="px-3 py-2 font-medium text-counsly-muted">College Count</th>
                        <th className="px-3 py-2 font-medium text-counsly-muted">Avg Fee</th>
                      </tr>
                    </thead>
                    <tbody>
                      {revenueData.breakdown.map((row, i) => (
                        <tr className="border-b border-counsly-line hover:bg-counsly-soft/50" key={i}>
                          <td className="px-3 py-2 font-medium text-counsly-ink">{row.college_type ?? "—"}</td>
                          <td className="px-3 py-2 text-counsly-ink">{formatCurrency(row.total_fees)}</td>
                          <td className="px-3 py-2 text-counsly-ink">{row.college_count ?? "—"}</td>
                          <td className="px-3 py-2 text-counsly-ink">{formatCurrency(row.avg_fee)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-counsly-muted">No breakdown data available.</p>
              )}
            </Surface>

            {/* Affordability tiers */}
            <Surface className="space-y-4 p-5" tone="paper">
              <div className="flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-counsly-coral" />
                <h2 className="font-display text-2xl text-counsly-ink">Affordability tiers</h2>
              </div>
              {revenueData?.affordability_tiers?.length ? (
                <div className="grid gap-3 sm:grid-cols-3">
                  {revenueData.affordability_tiers.map((tier) => (
                    <Surface className="space-y-3 p-4" key={tier.tier} tone={tier.tier === "affordable" ? "soft" : tier.tier === "premium" ? "dark" : "paper"}>
                      <Badge tone={tier.tier === "affordable" ? "safe" : tier.tier === "premium" ? "coral" : "warning"}>
                        {(tier.tier ?? "Unknown").toUpperCase()}
                      </Badge>
                      <p className="font-mono text-3xl font-semibold text-counsly-ink">{tier.college_count ?? "—"}</p>
                      <p className="text-sm text-counsly-body">colleges</p>
                      <div className="space-y-1 text-xs text-counsly-muted">
                        <p>Avg fee: {formatCurrency(tier.avg_fee)}</p>
                        <p>Range: {formatCurrency(tier.min_fee)} – {formatCurrency(tier.max_fee)}</p>
                      </div>
                    </Surface>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-counsly-muted">No affordability tier data available.</p>
              )}
            </Surface>

            {/* ROI scoring table */}
            <Surface className="space-y-4 p-5" tone="dark">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-counsly-coral" />
                <h2 className="font-display text-2xl text-white">ROI scoring</h2>
              </div>
              {revenueData?.roi_table?.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-counsly-slate">
                        <th className="px-3 py-2 font-medium text-counsly-card">College</th>
                        <th className="px-3 py-2 font-medium text-counsly-card">Avg Fee</th>
                        <th className="px-3 py-2 font-medium text-counsly-card">Avg Package</th>
                        <th className="px-3 py-2 font-medium text-counsly-card">ROI Score</th>
                        <th className="px-3 py-2 font-medium text-counsly-card">Tier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {revenueData.roi_table.map((row, i) => (
                        <tr className="border-b border-counsly-slate hover:bg-counsly-slate/50" key={i}>
                          <td className="px-3 py-2 font-medium text-white">
                            {row.college_name || row.college_code || "—"}
                          </td>
                          <td className="px-3 py-2 text-counsly-card">{formatCurrency(row.avg_fee)}</td>
                          <td className="px-3 py-2 text-counsly-card">{formatCurrency(row.avg_package)}</td>
                          <td className="px-3 py-2">
                            <Badge tone={(row.roi_score ?? 0) >= 80 ? "safe" : (row.roi_score ?? 0) >= 50 ? "warning" : "coral"}>
                              {row.roi_score != null ? `${row.roi_score.toFixed(1)}` : "—"}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 text-counsly-card">{row.tier ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-counsly-card">No ROI data available.</p>
              )}
            </Surface>
          </>
        )}
      </div>
    </FeatureGate>
  );
}