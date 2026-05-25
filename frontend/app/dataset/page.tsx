"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  Building2,
  CreditCard,
  FileText,
  MapPin,
  Route,
  School,
  Users,
} from "lucide-react";

import { FeatureGate } from "@/components/feature-gate";
import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import {
  fetchCreditHours,
  fetchDatasetOverview,
  fetchDistribution,
  fetchDistrictState,
  fetchFees,
  fetchMaster,
  fetchTransport,
} from "@/lib/api.mjs";

type Overview = {
  total_colleges?: number;
  total_branches?: number;
  total_cutoff_records?: number;
  total_students?: number;
  total_tfc_locations?: number;
  last_refreshed?: string;
};

type TabId = "fees" | "transport" | "district-state" | "master" | "distribution" | "credit-hours";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "fees", label: "Fees", icon: <CreditCard className="h-4 w-4" /> },
  { id: "transport", label: "Transport", icon: <Route className="h-4 w-4" /> },
  { id: "district-state", label: "District/State", icon: <MapPin className="h-4 w-4" /> },
  { id: "master", label: "Master", icon: <BookOpen className="h-4 w-4" /> },
  { id: "distribution", label: "Distribution", icon: <Building2 className="h-4 w-4" /> },
  { id: "credit-hours", label: "Credit Hours", icon: <FileText className="h-4 w-4" /> },
];

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
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TabContent({
  activeTab,
  data,
  filters,
  onFilterChange,
}: {
  activeTab: TabId;
  data: Record<string, unknown>[];
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
}) {
  const columnsByTab: Record<TabId, string[]> = {
    fees: ["college_code", "college_name", "branch_code", "fee_annual", "type"],
    transport: ["college_code", "college_name", "district", "hostel_available", "transport_available", "nearest_railway"],
    "district-state": ["district", "state", "college_count", "total_seats"],
    master: ["college_code", "college_name", "type", "district", "branch_code", "seats"],
    distribution: ["type", "count", "percentage"],
    "credit-hours": ["branch_code", "branch_name", "min_hours", "max_hours", "avg_hours"],
  };

  const columns = columnsByTab[activeTab];

  return (
    <div className="space-y-4">
      {(activeTab === "fees" || activeTab === "transport" || activeTab === "master") && (
        <div className="flex flex-wrap gap-3">
          {filters.district !== undefined && (
            <label className="field-label max-w-xs">
              District
              <input
                className="field"
                onChange={(e) => onFilterChange("district", e.target.value)}
                placeholder="Filter by district..."
                value={filters.district || ""}
              />
            </label>
          )}
          {activeTab === "fees" && (
            <label className="field-label max-w-xs">
              Type
              <input
                className="field"
                onChange={(e) => onFilterChange("type", e.target.value)}
                placeholder="Filter by type..."
                value={filters.type || ""}
              />
            </label>
          )}
          {activeTab === "transport" && (
            <>
              <label className="field-label max-w-[160px]">
                Hostel
                <select
                  className="field"
                  onChange={(e) => onFilterChange("hostel_available", e.target.value)}
                  value={filters.hostel_available || ""}
                >
                  <option value="">All</option>
                  <option value="true">Available</option>
                  <option value="false">Not Available</option>
                </select>
              </label>
              <label className="field-label max-w-[160px]">
                Transport
                <select
                  className="field"
                  onChange={(e) => onFilterChange("transport_available", e.target.value)}
                  value={filters.transport_available || ""}
                >
                  <option value="">All</option>
                  <option value="true">Available</option>
                  <option value="false">Not Available</option>
                </select>
              </label>
            </>
          )}
        </div>
      )}
      <Surface className="overflow-hidden p-4" tone="paper">
        <DataTable columns={columns} rows={data} />
      </Surface>
    </div>
  );
}

export default function DatasetPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("fees");
  const [tabData, setTabData] = useState<Record<string, unknown>[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  const [error, setError] = useState("");
  const [tabError, setTabError] = useState("");

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
        setError("Dataset overview could not be loaded.");
        setLoading(false);
      });
  }, []);

  const loadTabData = useCallback(
    (tab: TabId) => {
      setTabLoading(true);
      setTabError("");

      const fetchers: Record<TabId, () => Promise<Record<string, unknown>[]>> = {
        fees: () => fetchFees(filters) as Promise<Record<string, unknown>[]>,
        transport: () => fetchTransport(filters) as Promise<Record<string, unknown>[]>,
        "district-state": () => fetchDistrictState() as Promise<Record<string, unknown>[]>,
        master: () => fetchMaster(filters) as Promise<Record<string, unknown>[]>,
        distribution: () => fetchDistribution() as Promise<Record<string, unknown>[]>,
        "credit-hours": () => fetchCreditHours() as Promise<Record<string, unknown>[]>,
      };

      fetchers[tab]()
        .then((data) => {
          setTabData(Array.isArray(data) ? data : []);
          setTabLoading(false);
        })
        .catch(() => {
          setTabData([]);
          setTabError(`Failed to load ${tab} data.`);
          setTabLoading(false);
        });
    },
    [filters],
  );

  useEffect(() => {
    loadTabData(activeTab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const overviewItems = [
    { label: "Total Colleges", value: overview?.total_colleges ?? "—", icon: School },
    { label: "Total Branches", value: overview?.total_branches ?? "—", icon: BookOpen },
    { label: "Cutoff Records", value: overview?.total_cutoff_records ?? "—", icon: FileText },
    { label: "Students", value: overview?.total_students ?? "—", icon: Users },
    { label: "TFC Locations", value: overview?.total_tfc_locations ?? "—", icon: MapPin },
  ];

  return (
    <FeatureGate>
      <div className="space-y-6">
        <PageHeader
          description="Explore the full dataset powering the Counsly platform — fees, transport, districts, master records, distributions, and credit hours."
          eyebrow="Data Explorer"
          title="Dataset overview and details."
        />

        {loading && (
          <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
            Loading dataset overview...
          </p>
        )}

        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {overview && (
          <>
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
              {overviewItems.map((item) => (
                <Surface className="space-y-2 p-4" key={item.label} tone="paper">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-4 w-4 text-counsly-coral" />
                    <p className="eyebrow">{item.label}</p>
                  </div>
                  <p className="font-mono text-2xl font-semibold text-counsly-ink">{String(item.value)}</p>
                </Surface>
              ))}
            </div>

            {overview.last_refreshed && (
              <p className="text-xs text-counsly-muted">
                Last refreshed: {new Date(overview.last_refreshed).toLocaleString()}
              </p>
            )}
          </>
        )}

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

        {tabLoading && (
          <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
            Loading {activeTab} data...
          </p>
        )}

        {tabError && (
          <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{tabError}</span>
          </div>
        )}

        {!tabLoading && !tabError && (
          <TabContent
            activeTab={activeTab}
            data={tabData}
            filters={filters}
            onFilterChange={handleFilterChange}
          />
        )}
      </div>
    </FeatureGate>
  );
}