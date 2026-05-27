"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookmarkPlus, GitCompareArrows, Search } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { choiceWriteDestination } from "@/lib/access.mjs";
import { addChoice, searchColleges } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { branches, collegeCatalog, currency, districts, toneForBand, cleanCollegeName } from "@/lib/product";

export default function RecommendationsPage() {
  const { user } = useApp();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [branch, setBranch] = useState("");
  const [rows, setRows] = useState(collegeCatalog);
  const [status, setStatus] = useState("Loading fit-ranked recommendation rows.");
  const [added, setAdded] = useState("");

  useEffect(() => {
    const firstView = window.localStorage.getItem("counsly_recommendations_viewed") !== "true";
    if (firstView) {
      trackFunnelEvent("first_recommendation_viewed", {
        branch: branch || "all",
        district: district || "all",
        query: query || "",
        user,
      });
      window.localStorage.setItem("counsly_recommendations_viewed", "true");
    }
    searchColleges({ branch_code: branch || undefined, district: district || undefined, limit: 50, search: query || undefined })
      .then((results) => {
        setRows(results.length ? results : collegeCatalog);
        setStatus(results.length ? "Recommendations are fit-ranked by the live explorer search." : "No live fit rows matched. Showing preview targets.");
      })
      .catch(() => {
        setRows(collegeCatalog);
        setStatus("API recommendations are unavailable. Preview fit rows remain actionable.");
      });
  }, [branch, district, query]);

  const visible = rows;

  return (
    <div className="space-y-6">
      <PageHeader
        description="Safe, moderate, and ambitious choices grounded in fit-ranked search and current branch preferences."
        eyebrow="Recommendations"
        title="Start with evidence-backed targets."
      />

      <Surface className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_190px_240px]" tone="paper">
        <label className="field-label">
          Search
          <span className="relative">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-counsly-muted" />
            <input className="field pl-10" onChange={(event) => setQuery(event.target.value)} placeholder="College or district" value={query} />
          </span>
        </label>
        <label className="field-label">
          District
          <select className="field" onChange={(event) => setDistrict(event.target.value)} value={district}>
            <option value="">All</option>
            {districts.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="field-label">
          Branch
          <select className="field" onChange={(event) => setBranch(event.target.value)} value={branch}>
            <option value="">All branches</option>
            {branches.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
          </select>
        </label>
      </Surface>
      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{added || status}</p>

      <div className="grid gap-4 lg:grid-cols-3">
        {visible.map((college) => (
          <Surface className="flex flex-col justify-between gap-5 p-5" key={`${college.code}-${college.branchCode}`} tone="paper">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge tone={toneForBand(college.fitBand)}>{college.fitBand}</Badge>
                <span className="font-mono text-sm text-counsly-muted">Fit {college.fitScore}</span>
              </div>
              <div>
                <h2 className="font-display text-3xl text-counsly-ink">{cleanCollegeName(college.name)}</h2>
                <p className="mt-2 text-sm leading-6 text-counsly-body">{college.branchName} in {college.district}</p>
              </div>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-counsly-soft p-3">
                  <dt className="eyebrow">Cutoff</dt>
                  <dd className="font-mono text-lg text-counsly-ink">{college.cutoff || "Detail"}</dd>
                </div>
                <div className="rounded-lg bg-counsly-soft p-3">
                  <dt className="eyebrow">Annual fees</dt>
                  <dd className="font-mono text-lg text-counsly-ink">{college.fees ? currency(college.fees) : "Pending"}</dd>
                </div>
              </dl>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link className="button-primary flex-1" href={`/explore/${college.code}`}>Inspect <ArrowRight className="h-4 w-4" /></Link>
              <Link aria-label={`Compare ${cleanCollegeName(college.name)}`} className="button-secondary px-3" href={`/compare?focus=${college.code}&branches=${college.branchCode}`}>
                <GitCompareArrows className="h-4 w-4" />
              </Link>
              <button
                aria-label={`Add ${cleanCollegeName(college.name)} to choices`}
                className="button-secondary px-3"
                onClick={async () => {
                  const destination = choiceWriteDestination(user, "recommendations");
                  if (destination) {
                    router.push(destination);
                    return;
                  }
                  try {
                    await addChoice({ ...college, notes: "Added from recommendations." });
                    trackFunnelEvent("college_added", {
                      branch_code: college.branchCode,
                      college_code: college.code,
                      feature: "recommendations",
                      user,
                    });
                    setAdded(`${college.code} ${college.branchCode} added to the primary choice list.`);
                  } catch {
                    setAdded("The choice API is not reachable. Open college insight to continue in preview mode.");
                  }
                }}
                type="button"
              >
                <BookmarkPlus className="h-4 w-4" />
              </button>
            </div>
          </Surface>
        ))}
      </div>

    </div>
  );
}
