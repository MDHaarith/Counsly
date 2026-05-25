"use client";

import { useState } from "react";
import {
  AlertCircle,
  BarChart3,
  Download,
  FileText,
  GitCompareArrows,
  Layers,
  Loader2,
  TrendingUp,
} from "lucide-react";

import { FeatureGate } from "@/components/feature-gate";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { generateReport } from "@/lib/api.mjs";

type ReportType = "choice_list_summary" | "compare_summary" | "round_summary" | "financial_overview";

const REPORT_CARDS: {
  type: ReportType;
  title: string;
  description: string;
  icon: React.ReactNode;
}[] = [
  {
    type: "choice_list_summary",
    title: "Choice List Summary",
    description: "Overview of all choices, priorities, and fit bands in your current workspace.",
    icon: <Layers className="h-5 w-5" />,
  },
  {
    type: "compare_summary",
    title: "Compare Summary",
    description: "Consolidated comparison data across all saved compare sessions.",
    icon: <GitCompareArrows className="h-5 w-5" />,
  },
  {
    type: "round_summary",
    title: "Round Summary",
    description: "Round status, decisions made, and pending actions across active rounds.",
    icon: <BarChart3 className="h-5 w-5" />,
  },
  {
    type: "financial_overview",
    title: "Financial Overview",
    description: "Revenue projections, fee tiers, affordability analysis, and ROI scores.",
    icon: <TrendingUp className="h-5 w-5" />,
  },
];

export default function ReportingPage() {
  const [generating, setGenerating] = useState<ReportType | null>(null);
  const [result, setResult] = useState<{ report_type: ReportType; summary?: string } | null>(null);
  const [error, setError] = useState("");

  const handleGenerate = async (reportType: ReportType) => {
    setGenerating(reportType);
    setError("");
    setResult(null);

    try {
      const data = await generateReport(reportType);
      setResult({
        report_type: reportType,
        summary:
          typeof data === "string"
            ? data
            : data?.summary || data?.result || JSON.stringify(data, null, 2),
      });
    } catch {
      setError(`Failed to generate ${reportType.replace(/_/g, " ")}.`);
    } finally {
      setGenerating(null);
    }
  };

  const getReportTitle = (type: ReportType) => {
    return REPORT_CARDS.find((c) => c.type === type)?.title ?? type.replace(/_/g, " ");
  };

  return (
    <FeatureGate>
      <div className="space-y-6">
        <PageHeader
          description="Generate on-demand summaries for choice lists, compares, rounds, and financial data."
          eyebrow="Reporting"
          title="Generate reports from your workspace."
        />

        {/* Report type cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {REPORT_CARDS.map((card) => (
            <Surface className="flex flex-col gap-4 p-5" key={card.type} tone="paper">
              <div className="flex items-center gap-2">
                <span className="text-counsly-coral">{card.icon}</span>
                <h2 className="font-display text-xl text-counsly-ink">{card.title}</h2>
              </div>
              <p className="flex-1 text-sm leading-6 text-counsly-body">{card.description}</p>
              <button
                className="button-primary inline-flex items-center justify-center gap-2"
                disabled={generating != null}
                onClick={() => handleGenerate(card.type)}
              >
                {generating === card.type ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Generate
                  </>
                )}
              </button>
            </Surface>
          ))}
        </div>

        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Generated result */}
        {result && (
          <Surface className="space-y-4 p-6" tone="soft">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-counsly-coral" />
              <h2 className="font-display text-2xl text-counsly-ink">
                {getReportTitle(result.report_type)}
              </h2>
              <Badge tone="safe">Generated</Badge>
            </div>
            <div className="rounded-lg border border-counsly-line bg-counsly-canvas p-4">
              <p className="whitespace-pre-wrap text-sm leading-6 text-counsly-body">
                {result.summary || "Report generated successfully."}
              </p>
            </div>
          </Surface>
        )}
      </div>
    </FeatureGate>
  );
}