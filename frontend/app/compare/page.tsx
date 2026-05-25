"use client";

import { CSSProperties, Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, Sparkles } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, PremiumBoard, Surface } from "@/components/ui";
import { compareColleges, fetchAiCompareReasoning, fetchCompareSessions, saveCompareSession } from "@/lib/api.mjs";
import { collegeCatalog, currency } from "@/lib/product";

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

function fromPreview(code: string): CompareColumn | undefined {
  const college = collegeCatalog.find((item) => item.code === code);
  if (!college) return undefined;
  return {
    avg_package_lpa: college.averagePackage,
    code: college.code,
    cutoff_2025: college.cutoff,
    district: college.district,
    fee_structure_annual: college.fees,
    hostel_available: college.hostel,
    is_autonomous: college.autonomous,
    name: college.name,
    nba_accredited: college.nba,
    nearest_railway_distance_km: college.distanceKm,
    nearest_railway_station: college.railway,
    placement_rate_pct: college.placementRate,
    transport_available: college.transport,
    type: college.type,
    cutoff_marks_last_three: [college.cutoff - 1.2, college.cutoff - 0.5, college.cutoff],
  };
}

function CompareInner() {
  const params = useSearchParams();
  const { user } = useApp();
  const [saved, setSaved] = useState("");
  const focus = params.get("focus");
  const codes = useMemo(() => {
    const ids = params.get("ids");
    if (ids) return ids.split(",").filter(Boolean).slice(0, 4);
    return focus ? [focus, focus === "2006" ? "0001" : "2006"] : ["0001", "2006"];
  }, [focus, params]);
  const preview = useMemo(() => codes.map(fromPreview).filter(Boolean) as CompareColumn[], [codes]);
  const [colleges, setColleges] = useState<CompareColumn[]>(preview);
  const [sessions, setSessions] = useState<Array<{ href: string; id: string; title: string }>>([]);
  const [explanation, setExplanation] = useState("Comparing live college metrics before generating the rule-based summary.");
  const [aiReasoning, setAiReasoning] = useState("No AI reasoning has been requested yet.");
  const [status, setStatus] = useState("Loading compare metrics from the workspace API.");
  const template = { gridTemplateColumns: `minmax(130px,0.7fr) repeat(${Math.max(colleges.length, 1)}, minmax(180px,1fr))` } satisfies CSSProperties;

  useEffect(() => {
    const branchCodes = (params.get("branches")?.split(",").filter(Boolean) ?? codes.map((code) => collegeCatalog.find((college) => college.code === code)?.branchCode || "CS")).slice(0, codes.length);
    Promise.all([
      compareColleges(codes, branchCodes),
      fetchCompareSessions(),
      fetchAiCompareReasoning({
        colleges: codes.map((code) => collegeCatalog.find((college) => college.code === code)?.name || code),
        metrics: ["fees", "cutoff pressure", "district fit", "hostel", "transport"],
      }),
    ])
      .then(([payload, savedSessions, reasoning]) => {
        setColleges(payload.colleges);
        setSessions(savedSessions.slice(0, 4));
        setExplanation(payload.explanation);
        setAiReasoning(reasoning.reasoning);
        setStatus("Live compare metrics and saved compare sessions loaded from the workspace API.");
      })
      .catch(() => {
        setColleges(preview);
        setExplanation("Preview comparison stays available while live cutoff and deterministic summary data are unreachable.");
        setAiReasoning("No AI reasoning is available in preview mode. Use the visible metric rows as the decision basis.");
        setStatus("API compare unavailable. Showing preview metrics.");
      });
  }, [codes, preview]);

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

      <Surface className="overflow-hidden" tone="paper">
        <div className="grid border-b border-counsly-line bg-counsly-soft" style={template}>
          <p className="p-4 text-sm font-medium text-counsly-muted">Metric</p>
          {colleges.map((college) => (
            <div className="border-l border-counsly-line p-4" key={college.code}>
              <Badge>{college.code}</Badge>
              <h2 className="mt-3 font-display text-2xl text-counsly-ink">{college.name}</h2>
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
        <div className={user?.subscription_active ? "" : "relative"}>
          {!user?.subscription_active && <div className="absolute inset-0 z-10 bg-counsly-canvas/70 backdrop-blur-[3px]" />}
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

      <div className="grid gap-4 lg:grid-cols-2">
        <Surface className="space-y-4 p-6" tone="dark">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-counsly-coral" />
            <Badge tone="dark">Rule-based summary</Badge>
          </div>
          <p className="text-sm leading-7 text-counsly-card">{explanation}</p>
        </Surface>
        <Surface className="space-y-3 p-6" tone="paper">
          <h2 className="font-display text-3xl text-counsly-ink">AI compare reasoning</h2>
          <p className="text-sm leading-7 text-counsly-body">{aiReasoning}</p>
        </Surface>
      </div>

      {user?.subscription_active ? (
        <Surface className="space-y-3 p-6" tone="paper">
          <h2 className="font-display text-3xl text-counsly-ink">Premium rows</h2>
            <p className="text-sm leading-6 text-counsly-body">
              Railway distance, placement rate, and average package stay visible as fixed comparison rows in the 2027 workflow.
            </p>
        </Surface>
      ) : (
        <PremiumBoard
          body="Free compare previews the complete row structure. Placement and rail context unlock with Full Access, while the summary stays deterministic for everyone."
          title="Premium metric rows are blurred"
        />
      )}

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
