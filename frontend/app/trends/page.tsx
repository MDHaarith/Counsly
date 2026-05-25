"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertCircle, BarChart3, BookOpen, Layers, Users } from "lucide-react";

import { FeatureGate } from "@/components/feature-gate";
import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { fetchBranchState, fetchCommunityView, fetchCreditHourTrends } from "@/lib/api.mjs";

type TabId = "community-view" | "credit-hours" | "branch-state";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "community-view", label: "Community View", icon: <Users className="h-4 w-4" /> },
  { id: "credit-hours", label: "Credit Hours", icon: <BarChart3 className="h-4 w-4" /> },
  { id: "branch-state", label: "Branch State", icon: <BookOpen className="h-4 w-4" /> },
];

type CommunityRow = {
  community?: string;
  year?: number;
  avg_cutoff?: number;
};

type CreditHourRow = {
  branch_code?: string;
  branch_name?: string;
  duration_years?: number;
  college_count?: number;
};

type BranchStateRow = {
  branch_code?: string;
  branch_name?: string;
  total_seats?: number;
  college_count?: number;
  avg_cutoff?: number;
};

function DataTable({ columns, rows }: { columns: string[]; rows: Record<string, unknown>[] }) {
  if (!rows.length) {
    return <p className="py-6 text-center text-sm text-counsly-muted">No data available.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-counsly-line">
            {columns.map((col) => (
              <th className="px-3 py-2 font-medium text-counsly-muted" key={col}>
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr className="border-b border-counsly-line hover:bg-counsly-soft/50" key={i}>
              {columns.map((col) => (
                <td className="px-3 py-2 text-counsly-ink" key={col}>
                  {typeof row[col] === "number" ? Number(row[col]).toFixed(2) : String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TabContent({ activeTab, data }: { activeTab: TabId; data: Record<string, unknown>[] }) {
  const columnsByTab: Record<TabId, string[]> = {
    "community-view": ["community", "year", "avg_cutoff"],
    "credit-hours": ["branch_code", "branch_name", "duration_years", "college_count"],
    "branch-state": ["branch_code", "branch_name", "total_seats", "college_count", "avg_cutoff"],
  };

  const columns = columnsByTab[activeTab];

  return (
    <div className="space-y-4">
      <Surface className="overflow-hidden p-4" tone="paper">
        <DataTable columns={columns} rows={data} />
      </Surface>
    </div>
  );
}

export default function TrendsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("community-view");
  const [tabData, setTabData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadTabData = useCallback(
    async (tab: TabId) => {
      setLoading(true);
      setError("");

      const fetchers: Record<TabId, () => Promise<Record<string, unknown>[]>> = {
        "community-view": () => fetchCommunityView() as Promise<Record<string, unknown>[]>,
        "credit-hours": () => fetchCreditHourTrends() as Promise<Record<string, unknown>[]>,
        "branch-state": () => fetchBranchState() as Promise<Record<string, unknown>[]>,
      };

      try {
        const data = await fetchers[tab]();
        setTabData(Array.isArray(data) ? data : []);
      } catch {
        setTabData([]);
        setError(`Failed to load ${tab} data.`);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab, loadTabData]);

  return (
    <FeatureGate>
      <div className="space-y-6">
        <PageHeader
          description="Cutoff trends by community, credit hour distribution, and branch-level aggregates across all years."
          eyebrow="Trend Analytics"
          title="Historical patterns and branch insights."
        />

        {/* Tab navigation */}
        <Surface className="p-4" tone="soft">
          <nav className="flex flex-wrap gap-1">
            {TABS.map((tab) => (
              <button
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-counsly-ink text-counsly-canvas"
                    : "text-counsly-body hover:bg-counsly-card"
                }`}
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </Surface>

        {loading && (
          <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
            Loading {activeTab} data...
          </p>
        )}

        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && <TabContent activeTab={activeTab} data={tabData} />}
      </div>
    </FeatureGate>
  );
}