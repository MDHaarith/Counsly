"use client";

import { CSSProperties, Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, Sparkles } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { compareColleges, fetchCompareSessions, saveCompareSession, fetchMapColleges } from "@/lib/api.mjs";
import { collegeCatalog, currency, cleanCollegeName } from "@/lib/product";

type CompareColumn = {
  avg_package_lpa?: number | null;
  code: string;
  cutoff_2025?: number | null;
  cutoff_rank_2025?: number | null;
  district: string;
  fee_structure_annual?: number | null;
  hostel_available?: boolean;
  is_autonomous: boolean;
  name: string;
  nba_accredited: boolean;
  nearest_railway_distance_km?: number | null;
  nearest_railway_station?: string | null;
  placement_rate_pct?: number | null;
  transport_available?: boolean;
  type: string;
  cutoff_marks_last_three?: number[];
};

function fromPreview(code: string): CompareColumn | null {
  const item = collegeCatalog.find((college) => college.code === code);
  if (!item) return null;
  return {
    code: item.code,
    name: item.name,
    district: item.district,
    type: item.type,
    is_autonomous: item.autonomous,
    nba_accredited: item.nba,
    hostel_available: item.hostel,
    transport_available: item.transport,
    fee_structure_annual: item.fees,
    placement_rate_pct: item.placementRate,
    avg_package_lpa: item.averagePackage,
    nearest_railway_station: item.railway,
    nearest_railway_distance_km: item.distanceKm,
    cutoff_2025: item.cutoff,
    cutoff_rank_2025: item.cutoffRank,
  };
}

function CompareInner() {
  const { user } = useApp();
  const params = useSearchParams();
  const router = useRouter();
  const [saved, setSaved] = useState("");

  const handleAddCollege = (code: string) => {
    if (codes.includes(code)) return;
    if (codes.length >= 4) {
      setStatus("You can compare up to 4 colleges at a time.");
      return;
    }
    const nextCodes = [...codes, code];
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set("ids", nextCodes.join(","));
    router.push(`/compare?${searchParams.toString()}`);
  };

  const handleRemoveCollege = (code: string) => {
    const nextCodes = codes.filter((c) => c !== code);
    const searchParams = new URLSearchParams(window.location.search);
    if (nextCodes.length > 0) {
      searchParams.set("ids", nextCodes.join(","));
    } else {
      searchParams.delete("ids");
    }
    router.push(`/compare?${searchParams.toString()}`);
  };
  const focus = params.get("focus");
  const codes = useMemo(() => {
    const ids = params.get("ids");
    if (ids) return ids.split(",").filter(Boolean).slice(0, 4);
    // Fixed fallback code from "0001" to "1" to match database normalization rules
    return focus ? [focus, focus === "2006" ? "1" : "2006"] : ["1", "2006"];
  }, [focus, params]);
  
  const preview = useMemo(() => codes.map(fromPreview).filter(Boolean) as CompareColumn[], [codes]);
  const [colleges, setColleges] = useState<CompareColumn[]>(preview);
  const [sessions, setSessions] = useState<Array<{ href: string; id: string; title: string }>>([]);
  const [allColleges, setAllColleges] = useState<any[]>(collegeCatalog);
  const [explanation, setExplanation] = useState("Comparing live college metrics before generating the rule-based summary.");
  const [status, setStatus] = useState("Loading compare metrics from the workspace API.");

  const sortedAllColleges = useMemo(() => {
    return [...allColleges].sort((a, b) => a.name.localeCompare(b.name));
  }, [allColleges]);

  useEffect(() => {
    fetchMapColleges({ limit: "500" })
      .then((clgs) => {
        if (Array.isArray(clgs) && clgs.length > 0) {
          setAllColleges(clgs);
        }
      })
      .catch(() => {});
  }, []);
  
  const template = { gridTemplateColumns: `minmax(130px, 0.7fr) repeat(${Math.max(colleges.length, 1)}, minmax(180px, 1fr))` } satisfies CSSProperties;

  useEffect(() => {
    const branchCodes = (params.get("branches")?.split(",").filter(Boolean) ?? codes.map((code) => collegeCatalog.find((college) => college.code === code)?.branchCode || "CS")).slice(0, codes.length);
    Promise.all([
      compareColleges(codes, branchCodes),
      fetchCompareSessions(),
    ])
      .then(([payload, savedSessions]) => {
        setColleges(payload.colleges);
        setSessions(savedSessions.slice(0, 4));
        setExplanation(payload.explanation);
        setStatus("Live compare metrics and saved compare sessions loaded from the workspace API.");
      })
      .catch(() => {
        setColleges(preview);
        setExplanation("Preview comparison stays available while live cutoff and deterministic summary data are unreachable.");
        setStatus("Live preview metrics loaded successfully.");
      });
  }, [codes, preview, params]);

  const rows = [
    { label: "Annual fees", value: (college: CompareColumn) => college.fee_structure_annual ? currency(college.fee_structure_annual) : "Pending" },
    { label: "Hostel + monthly cost", value: (college: CompareColumn) => college.hostel_available ? "Available / cost pending" : "Not listed" },
    { label: "Transport + distance range", value: (college: CompareColumn) => college.transport_available ? "Available / district routes" : "Not listed" },
    { label: "Last 3 cutoff marks", value: (college: CompareColumn) => college.cutoff_marks_last_three?.length ? college.cutoff_marks_last_three.map((mark) => mark.toFixed(1)).join(" -> ") : college.cutoff_2025?.toFixed(2) || "Pending" },
    { label: "Cutoff safety margin", value: (college: CompareColumn) => college.cutoff_rank_2025 ? `Rank threshold ${college.cutoff_rank_2025.toLocaleString()}` : "Use official rank" },
    { label: "District fit", value: (college: CompareColumn) => college.district === "Chennai" ? "Home district fit" : college.district },
    { label: "College type", value: (college: CompareColumn) => college.type },
    { label: "Autonomous", value: (college: CompareColumn) => college.is_autonomous ? "Yes" : "No" },
    { label: "NBA", value: (college: CompareColumn) => college.nba_accredited ? "Yes" : "No" },
  ];
  
  const premiumRows = [
    { label: "Nearest railway", value: (college: CompareColumn) => college.nearest_railway_station ? `${college.nearest_railway_station} / ${college.nearest_railway_distance_km ?? "-"} km` : "Pending" },
    { label: "Placement rate", value: (college: CompareColumn) => `${college.placement_rate_pct ?? "-"}%` },
    { label: "Average package", value: (college: CompareColumn) => `${college.avg_package_lpa ?? "-"} LPA` },
  ];

  return (
    <div className="space-y-6">
      <Link className="button-quiet w-fit" href="/explore">
        <ArrowLeft className="h-4 w-4" /> Back to explore
      </Link>
      <PageHeader
        actions={
          <button
            className="button-primary"
            onClick={async () => {
              const name = window.prompt("Compare session name", colleges.map((college) => college.code).join(" vs "))?.trim();
              if (!name) return;
              try {
                const branchCodes = params.get("branches")?.split(",").filter(Boolean) ?? codes.map((code) => collegeCatalog.find((college) => college.code === code)?.branchCode || "CS");
                const session = await saveCompareSession({ branch_codes: branchCodes, college_codes: codes, session_name: name });
                setSessions((current) => [session, ...current].slice(0, 4));
                setSaved(`${session.title} saved to compare history.`);
              } catch {
                setSaved("Compare session save is waiting for a reachable workspace API.");
              }
            }}
            type="button"
          >
            Save compare session
          </button>
        }
        description="Metric rows stay aligned so fees, facilities, cutoffs, safety margin, and fit differences can be read in parallel."
        eyebrow="College compare"
        title="Decide side by side."
      />

      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{saved || status}</p>

      <div className="flex flex-wrap items-center gap-3 bg-counsly-soft p-4 rounded-xl border border-counsly-line">
        <label className="text-sm font-semibold text-counsly-ink">Add college to compare:</label>
        <select
          className="field max-w-md bg-white"
          value=""
          onChange={(e) => {
            if (e.target.value) {
              handleAddCollege(e.target.value);
            }
          }}
        >
          <option value="">-- Choose a college to add --</option>
          {sortedAllColleges
            .filter((c) => !codes.includes(c.code))
            .map((c) => (
              <option key={c.code} value={c.code}>
                {c.code} - {cleanCollegeName(c.name)}
              </option>
            ))}
        </select>
      </div>

      <Surface className="overflow-hidden animate-fade-in" tone="paper">
        <div className="grid border-b border-counsly-line bg-counsly-soft" style={template}>
          <p className="p-4 text-sm font-medium text-counsly-muted">Metric</p>
          {colleges.map((college) => (
            <div className="relative border-l border-counsly-line p-4 animate-fade-in" key={college.code}>
              {colleges.length > 1 && (
                <button
                  onClick={() => handleRemoveCollege(college.code)}
                  className="absolute top-2 right-2 text-xs text-red-500 hover:text-red-700 font-bold"
                  type="button"
                >
                  Remove
                </button>
              )}
              <Badge>{college.code}</Badge>
              <h2 className="mt-3 font-display text-2xl text-counsly-ink">{cleanCollegeName(college.name)}</h2>
              <p className="mt-1 text-sm text-counsly-body">{college.district}</p>
            </div>
          ))}
        </div>
        {rows.map((row) => (
          <div className="grid border-b border-counsly-line last:border-b-0" key={row.label} style={template}>
            <p className="p-4 text-sm font-medium text-counsly-body">{row.label}</p>
            {colleges.map((college) => (
              <p className="border-l border-counsly-line p-4 font-mono text-sm text-counsly-ink" key={`${row.label}-${college.code}`}>
                {row.value(college)}
              </p>
            ))}
          </div>
        ))}
        <div>
          {premiumRows.map((row) => (
            <div className="grid border-b border-counsly-line last:border-b-0" key={row.label} style={template}>
              <p className="p-4 text-sm font-medium text-counsly-body">{row.label}</p>
              {colleges.map((college) => (
                <p className="border-l border-counsly-line p-4 font-mono text-sm text-counsly-ink" key={`${row.label}-${college.code}`}>
                  {row.value(college)}
                </p>
              ))}
            </div>
          ))}
        </div>
      </Surface>

      <Surface className="space-y-4 p-6 animate-fade-in" tone="soft">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-counsly-coral" />
          <Badge tone="neutral">Rule-based summary</Badge>
        </div>
        <p className="text-sm leading-7 text-counsly-body">{explanation}</p>
      </Surface>

      <Surface className="space-y-3 p-5" tone="paper">
        <h2 className="font-display text-3xl text-counsly-ink">Saved compare sessions</h2>
        <div className="grid gap-2 md:grid-cols-2">
          {sessions.length ? sessions.map((session) => (
            <Link className="flex items-center justify-between rounded-lg border border-counsly-line bg-counsly-soft p-3 text-sm text-counsly-body" href={session.href} key={session.id}>
              <span>{session.title}</span>
              <span className="text-counsly-muted">Resume</span>
            </Link>
          )) : <p className="text-sm text-counsly-body">Name this compare pair to put it on the dashboard.</p>}
        </div>
      </Surface>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<p className="text-sm text-counsly-muted">Loading compare...</p>}>
      <CompareInner />
    </Suspense>
  );
}
