"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BookmarkPlus, GitCompareArrows, Search } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface, EmptyState, StatusToast } from "@/components/ui";
import { FeatureGate } from "@/components/feature-gate";
import { choiceWriteDestination } from "@/lib/access.mjs";
import { addChoice, searchColleges } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { branches, collegeCatalog, currency, districts, toneForBand, cleanCollegeName } from "@/lib/product";

function RecommendationsContent() {
  const { user } = useApp();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [branch, setBranch] = useState("");
  const [rows, setRows] = useState(collegeCatalog);
  const [toast, setToast] = useState<{ message: string; tone: "success" | "error" | "default" } | null>(null);

  const showToast = (message: string, tone: "success" | "error" | "default" = "default") => {
    setToast({ message, tone });
  };

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

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
        showToast(results.length ? "Recommendations loaded." : "No exact matches. Showing preview.", "success");
      })
      .catch(() => {
        setRows(collegeCatalog);
        showToast("Recommendations offline. Using local catalog.", "default");
      });
  }, [branch, district, query, user]);

  const visible = rows;

  return (
    <div className="space-y-8 relative">
      {toast && (
        <div className="fixed bottom-24 right-6 z-50 animate-slide-up">
          <StatusToast message={toast.message} tone={toast.tone} />
        </div>
      )}

      <PageHeader
        description="Discover fit-ranked college recommendations customized to your academic aggregate and preferred branches."
        eyebrow="Recommendations"
        title="Start with evidence-backed targets."
      />

      <Surface className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_190px_240px]" tone="paper">
        <label className="field-label">
          Search
          <span className="relative mt-1 block">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-counsly-muted" />
            <input className="field pl-10" onChange={(event) => setQuery(event.target.value)} placeholder="College or district" value={query} />
          </span>
        </label>
        <label className="field-label">
          District
          <select className="field mt-1" onChange={(event) => setDistrict(event.target.value)} value={district}>
            <option value="">All districts</option>
            {districts.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="field-label">
          Branch
          <select className="field mt-1" onChange={(event) => setBranch(event.target.value)} value={branch}>
            <option value="">All branches</option>
            {branches.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
          </select>
        </label>
      </Surface>

      {visible.length === 0 ? (
        <Surface className="p-10 flex flex-col items-center justify-center min-h-[300px]" tone="paper">
          <EmptyState
            icon={<Search className="h-8 w-8" />}
            title="No recommendations found"
            description="Adjust your search filters or change your community/mark settings to view eligible recommendations."
            action={
              <button
                onClick={() => {
                  setQuery("");
                  setDistrict("");
                  setBranch("");
                }}
                className="button-secondary mt-4"
              >
                Reset filters
              </button>
            }
          />
        </Surface>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {visible.map((college) => (
            <Surface className="flex flex-col justify-between gap-5 p-5 hover:border-counsly-coral transition-colors" key={`${college.code}-${college.branchCode}`} tone="paper">
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-2 flex-nowrap">
                  <Badge tone={toneForBand(college.fitBand)}>{college.fitBand} Fit</Badge>
                  <span className="font-mono text-xs font-semibold text-counsly-muted bg-counsly-soft/80 border border-counsly-line px-2 py-0.5 rounded shrink-0">Fit {college.fitScore}</span>
                </div>
                <div>
                  <h2 className="font-display text-xl font-semibold text-counsly-ink">{cleanCollegeName(college.name)}</h2>
                  <p className="mt-1.5 text-xs text-counsly-muted">{college.branchName} in {college.district}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <Link 
                    href={`/explore/${college.code}?tab=Cutoffs`}
                    className="rounded-lg bg-counsly-soft/40 border border-counsly-line p-2.5 flex flex-col justify-between transition duration-200 hover:border-counsly-coral hover:bg-counsly-soft"
                  >
                    <span className="text-counsly-muted font-medium">Cutoff</span>
                    <strong className="font-mono text-sm font-semibold text-counsly-ink mt-0.5">{college.cutoff || "Detail"}</strong>
                  </Link>
                  <Link 
                    href={`/explore/${college.code}?tab=Fees & Facilities`}
                    className="rounded-lg bg-counsly-soft/40 border border-counsly-line p-2.5 flex flex-col justify-between transition duration-200 hover:border-counsly-coral hover:bg-counsly-soft"
                  >
                    <span className="text-counsly-muted font-medium">Annual Fees</span>
                    <strong className="font-mono text-sm font-semibold text-counsly-ink mt-0.5">{college.fees ? currency(college.fees) : "Pending"}</strong>
                  </Link>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-counsly-line/80">
                <Link className="button-primary flex-1 justify-center" href={`/explore/${college.code}`}>Inspect <ArrowRight className="h-4 w-4" /></Link>
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
                      showToast(`${college.code} added to choices.`, "success");
                    } catch {
                      showToast("Error adding choice. Offline mode.", "error");
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
      )}
    </div>
  );
}

export default function RecommendationsPage() {
  return (
    <FeatureGate>
      <RecommendationsContent />
    </FeatureGate>
  );
}
