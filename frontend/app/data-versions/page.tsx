"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CalendarClock, Database, ExternalLink, RefreshCw } from "lucide-react";
import Link from "next/link";

import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { fetchDatasetOverview } from "@/lib/api.mjs";

type DatasetFreshness = {
  dataset: string;
  last_refreshed?: string;
  row_count?: number;
  status?: string;
};

type Overview = {
  total_colleges?: number;
  total_branches?: number;
  total_cutoff_records?: number;
  total_students?: number;
  total_tfc_locations?: number;
  last_refreshed?: string;
  datasets?: DatasetFreshness[];
};

const DATASET_LABELS: Record<string, string> = {
  cutoff_data: "Cutoff Data",
  seat_matrix: "Seat Matrix",
  college_master: "College Master",
  rank_list: "Rank List",
  fee_structure: "Fee Structure",
  transport_data: "Transport Data",
  tfc_locations: "TFC Locations",
  branch_data: "Branch Data",
};

export default function DataVersionsPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    fetchDatasetOverview()
      .then((data: Overview) => {
        setOverview(data);
        setLoading(false);
      })
      .catch(() => {
        setOverview(null);
        setError("Data freshness information could not be loaded.");
        setLoading(false);
      });
  }, []);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "—";
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const datasets = overview?.datasets ?? [];

  // Build dataset list from the overview fields or from the datasets array
  const datasetEntries: DatasetFreshness[] =
    datasets.length > 0
      ? datasets
      : Object.keys(DATASET_LABELS).map((key) => ({
          dataset: key,
          last_refreshed: overview?.last_refreshed,
          row_count: undefined,
          status: "unknown",
        }));

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link className="button-secondary" href="/admin">
            <RefreshCw className="h-4 w-4" /> Go to admin updates
          </Link>
        }
        description="Track the freshness and version status of all datasets powering the Counsly platform."
        eyebrow="Data Freshness"
        title="How recent is the data?"
      />

      {loading && (
        <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
          Loading data freshness information...
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
          {/* Overview metrics */}
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            <Metric label="Colleges" value={String(overview?.total_colleges ?? "—")} note="In current dataset" />
            <Metric label="Branches" value={String(overview?.total_branches ?? "—")} note="Active branches" />
            <Metric label="Cutoff Records" value={String(overview?.total_cutoff_records ?? "—")} note="Historical" />
            <Metric label="Students" value={String(overview?.total_students ?? "—")} note="In database" />
            <Metric label="TFC Locations" value={String(overview?.total_tfc_locations ?? "—")} note="Service centres" />
          </div>

          {/* Global refresh date */}
          {overview?.last_refreshed && (
            <Surface className="flex items-center gap-3 p-4" tone="soft">
              <CalendarClock className="h-5 w-5 text-counsly-coral" />
              <div>
                <p className="text-sm font-medium text-counsly-ink">Last global refresh</p>
                <p className="text-sm text-counsly-muted">{formatDate(overview.last_refreshed)}</p>
              </div>
            </Surface>
          )}

          {/* Per-dataset freshness */}
          <h2 className="font-display text-2xl text-counsly-ink">Dataset freshness</h2>

          <Surface className="overflow-hidden" tone="paper">
            {datasetEntries.length === 0 ? (
              <div className="p-6 text-center text-sm text-counsly-muted">
                No dataset freshness information available.
              </div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-counsly-line">
                    <th className="px-4 py-3 font-medium text-counsly-muted">Dataset</th>
                    <th className="px-4 py-3 font-medium text-counsly-muted">Last Refreshed</th>
                    <th className="px-4 py-3 font-medium text-counsly-muted">Row Count</th>
                    <th className="px-4 py-3 font-medium text-counsly-muted">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {datasetEntries.map((entry) => (
                    <tr className="border-b border-counsly-line hover:bg-counsly-soft/50" key={entry.dataset}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Database className="h-4 w-4 text-counsly-coral" />
                          <span className="font-medium text-counsly-ink">
                            {DATASET_LABELS[entry.dataset] || entry.dataset.replace(/_/g, " ")}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-counsly-body">{formatDate(entry.last_refreshed)}</td>
                      <td className="px-4 py-3 font-mono text-counsly-body">
                        {entry.row_count != null ? entry.row_count.toLocaleString() : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={entry.status === "fresh" ? "safe" : entry.status === "stale" ? "warning" : "neutral"}>
                          {entry.status ?? "unknown"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Surface>

          {/* Admin link */}
          <Surface className="flex items-center justify-between gap-4 p-5" tone="dark">
            <div>
              <h3 className="font-display text-xl text-white">Need to update the data?</h3>
              <p className="mt-1 text-sm text-counsly-card">
                Head to the admin panel to record manual updates or queue scraping jobs.
              </p>
            </div>
            <Link className="button-primary shrink-0" href="/admin">
              <ExternalLink className="h-4 w-4" /> Admin panel
            </Link>
          </Surface>
        </>
      )}
    </div>
  );
}