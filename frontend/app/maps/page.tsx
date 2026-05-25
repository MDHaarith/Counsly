"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Globe,
  MapPin,
  Navigation,
  Search,
} from "lucide-react";

import { FeatureGate } from "@/components/feature-gate";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { fetchMapColleges, fetchTfcLocations } from "@/lib/api.mjs";

type TabId = "colleges" | "tfc";

const TABS: { id: TabId; label: string }[] = [
  { id: "colleges", label: "College Locations" },
  { id: "tfc", label: "TFC Locations" },
];

type LocationRow = {
  college_code?: string;
  college_name?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  district?: string;
};

type TfcLocationRow = {
  tfc_id?: string;
  name?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  city?: string;
};

function CoordsCard({
  lat,
  lng,
  label,
}: {
  lat: number | undefined | null;
  lng: number | undefined | null;
  label: string;
}) {
  return (
    <div className="rounded-lg bg-counsly-slate p-4 text-sm">
      <div className="mb-2 flex items-center gap-2">
        <Navigation className="h-4 w-4 text-counsly-coral" />
        <span className="font-medium text-white">{label}</span>
      </div>
      {lat != null && lng != null ? (
        <div className="space-y-1 font-mono text-xs text-counsly-card">
          <p>
            Lat: <span className="text-white">{lat.toFixed(6)}</span>
          </p>
          <p>
            Lng: <span className="text-white">{lng.toFixed(6)}</span>
          </p>
          <a
            className="mt-2 inline-flex items-center gap-1 text-counsly-teal underline hover:no-underline"
            href={`https://www.google.com/maps?q=${lat},${lng}`}
            rel="noopener noreferrer"
            target="_blank"
          >
            <MapPin className="h-3 w-3" /> Open in Maps
          </a>
        </div>
      ) : (
        <p className="text-xs text-counsly-card">Coordinates not available</p>
      )}
    </div>
  );
}

function MapGrid({
  collegeRows,
  tfcRows,
  activeTab,
  searchQuery,
  onSearchChange,
}: {
  collegeRows: LocationRow[];
  tfcRows: TfcLocationRow[];
  activeTab: TabId;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}) {
  const rows =
    activeTab === "colleges"
      ? collegeRows.map((r) => ({
          id: r.college_code || r.college_name || "",
          name: r.college_name || r.college_code || "—",
          address: r.address || r.district || "—",
          lat: r.latitude,
          lng: r.longitude,
          sub: r.district || "",
        }))
      : tfcRows.map((r) => ({
          id: r.tfc_id || r.name || "",
          name: r.name || r.tfc_id || "—",
          address: r.address || r.city || "—",
          lat: r.latitude,
          lng: r.longitude,
          sub: r.city || "",
        }));

  const filtered = searchQuery
    ? rows.filter(
        (r) =>
          r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          r.address.toLowerCase().includes(searchQuery.toLowerCase()) ||
          r.sub.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : rows;

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-counsly-muted" />
        <input
          className="field pl-9"
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={`Search ${activeTab === "colleges" ? "colleges" : "TFC locations"}...`}
          value={searchQuery}
        />
      </div>

      {filtered.length === 0 ? (
        <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-8 text-center text-sm text-counsly-muted">
          {searchQuery ? "No results match your search." : `No ${activeTab === "colleges" ? "college" : "TFC"} location data available.`}
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((item) => (
            <Surface className="space-y-3 p-4" key={item.id} tone="paper">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="font-medium text-counsly-ink truncate">{item.name}</h3>
                  <p className="text-xs text-counsly-muted truncate">{item.address}</p>
                </div>
                <Globe className="h-4 w-4 shrink-0 text-counsly-coral" />
              </div>
              <CoordsCard label="Coordinates" lat={item.lat} lng={item.lng} />
            </Surface>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MapsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("colleges");
  const [collegeRows, setCollegeRows] = useState<LocationRow[]>([]);
  const [tfcRows, setTfcRows] = useState<TfcLocationRow[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = useCallback(async (tab: TabId) => {
    setLoading(true);
    setError("");
    try {
      if (tab === "colleges") {
        const data = await fetchMapColleges({ limit: "500" });
        setCollegeRows(Array.isArray(data) ? data : []);
      } else {
        const data = await fetchTfcLocations({ limit: "500" });
        setTfcRows(Array.isArray(data) ? data : []);
      }
    } catch {
      setCollegeRows([]);
      setTfcRows([]);
      setError(`Failed to load ${tab === "colleges" ? "college" : "TFC"} locations.`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Load both tabs on mount
    setLoading(true);
    Promise.all([
      fetchMapColleges({ limit: "500" }).catch(() => []),
      fetchTfcLocations({ limit: "500" }).catch(() => []),
    ])
      .then(([clgs, tfcs]) => {
        setCollegeRows(Array.isArray(clgs) ? clgs : []);
        setTfcRows(Array.isArray(tfcs) ? tfcs : []);
        setLoading(false);
      })
      .catch(() => {
        setError("Could not load location data.");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    // If switching to a tab that hasn't loaded yet
    if (activeTab === "colleges" && collegeRows.length === 0 && !loading) {
      loadData("colleges");
    }
    if (activeTab === "tfc" && tfcRows.length === 0 && !loading) {
      loadData("tfc");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  return (
    <FeatureGate>
      <div className="space-y-6">
        <PageHeader
          description="Browse college and TFC locations with coordinates, addresses, and direct links to Google Maps."
          eyebrow="Location Maps"
          title="Find colleges and TFC centres."
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
                onClick={() => {
                  setActiveTab(tab.id);
                  setSearchQuery("");
                }}
              >
                <MapPin className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </Surface>

        {loading && (
          <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">
            Loading location data...
          </p>
        )}

        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-counsly-line bg-counsly-soft px-4 py-3 text-sm text-counsly-coral">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && (
          <MapGrid
            activeTab={activeTab}
            collegeRows={collegeRows}
            tfcRows={tfcRows}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />
        )}
      </div>
    </FeatureGate>
  );
}