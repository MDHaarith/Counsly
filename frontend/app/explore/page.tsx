"use client";

import { useDeferredValue, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Search, ShieldAlert } from "lucide-react";

import { Badge, PageHeader, Surface, EmptyState, StatusToast } from "@/components/ui";
import { searchColleges } from "@/lib/api.mjs";
import { branches, collegeCatalog, districts, toneForBand, cleanCollegeName } from "@/lib/product";

export default function ExplorePage() {
  const [search, setSearch] = useState("");
  const [district, setDistrict] = useState("");
  const [branch, setBranch] = useState("");
  const [sort, setSort] = useState<"fit" | "name" | "code">("fit");
  const [results, setResults] = useState(collegeCatalog);
  const [toast, setToast] = useState<{ message: string; tone: "success" | "error" | "default" } | null>(null);
  
  const deferredSearch = useDeferredValue(search.trim().toLowerCase());
  
  const colleges = results.filter((college) => {
    const searchable = `${college.code} ${college.name} ${college.district}`.toLowerCase();
    return (
      (!deferredSearch || searchable.includes(deferredSearch)) &&
      (!district || college.district === district) &&
      (!branch || college.branchCode === branch)
    );
  }).slice().sort((left, right) => {
    if (sort === "name") return left.name.localeCompare(right.name);
    if (sort === "code") return left.code.localeCompare(right.code);
    return right.fitScore - left.fitScore;
  });

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
    let active = true;
    searchColleges({
      branch_code: branch || undefined,
      district: district || undefined,
      limit: 50,
      search: deferredSearch || undefined,
    })
      .then((rows) => {
        if (!active) return;
        setResults(rows.length ? rows : collegeCatalog);
        showToast(rows.length ? "Matches found." : "Using offline catalog.", "success");
      })
      .catch(() => {
        if (!active) return;
        setResults(collegeCatalog);
        showToast("Live search unavailable. Local catalog active.", "default");
      });

    return () => {
      active = false;
    };
  }, [branch, deferredSearch, district]);

  return (
    <div className="space-y-8 relative">
      {toast && (
        <div className="fixed bottom-24 right-6 z-50 animate-slide-up">
          <StatusToast message={toast.message} tone={toast.tone} />
        </div>
      )}

      <PageHeader
        description="Search and filter TNEA colleges by cutoff, branch, and district to find your ideal fit."
        eyebrow="College explorer"
        title="Begin with colleges worth deciding on."
      />

      <Surface className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_190px_230px_180px]" tone="paper">
        <label className="field-label">
          Search college or code
          <span className="relative mt-1 block">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-counsly-muted" />
            <input className="field pl-10" onChange={(event) => setSearch(event.target.value)} placeholder="CEG, PSG, Chennai..." value={search} />
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
        <label className="field-label">
          Sort
          <select className="field mt-1" onChange={(event) => setSort(event.target.value as typeof sort)} value={sort}>
            <option value="fit">Fit ranked</option>
            <option value="name">Alphabetical</option>
            <option value="code">College code</option>
          </select>
        </label>
      </Surface>

      {colleges.length === 0 ? (
        <Surface className="p-10 flex flex-col items-center justify-center min-h-[300px]" tone="paper">
          <EmptyState
            icon={<Search className="h-8 w-8" />}
            title="No colleges match your filters"
            description="Try adjusting your search query, selecting a different district, or removing the branch filter."
            action={
              <button
                onClick={() => {
                  setSearch("");
                  setDistrict("");
                  setBranch("");
                }}
                className="button-secondary mt-4"
              >
                Reset all filters
              </button>
            }
          />
        </Surface>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {colleges.map((college) => (
            <Surface className="space-y-4 p-5 flex flex-col justify-between hover:border-counsly-coral transition-colors" key={`${college.code}-${college.branchCode}`} tone="paper">
              <div className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2 flex-nowrap">
                    <div className="flex items-center gap-2 flex-nowrap">
                      <Badge tone="dark">{college.code}</Badge>
                      <Badge tone={toneForBand(college.fitBand)}>{college.fitBand} fit</Badge>
                    </div>
                    <span className="font-mono text-xs font-semibold text-counsly-muted bg-counsly-soft/80 border border-counsly-line px-2 py-0.5 rounded shrink-0">
                      Fit {college.fitScore}
                    </span>
                  </div>
                  <div>
                    <h2 className="font-display text-xl font-semibold text-counsly-ink">{cleanCollegeName(college.name)}</h2>
                    <p className="mt-1 text-xs text-counsly-muted">
                      {college.branchName} in {college.district}
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                  <Link 
                    href={`/explore/${college.code}?tab=Cutoffs`}
                    className="rounded-lg bg-counsly-soft/40 border border-counsly-line p-2.5 flex flex-col justify-between transition duration-200 hover:border-counsly-coral hover:bg-counsly-soft"
                  >
                    <span className="text-counsly-muted font-medium">Cutoff</span>
                    <strong className="font-mono text-sm font-semibold text-counsly-ink mt-0.5">{college.cutoff}</strong>
                  </Link>
                  <Link 
                    href={`/explore/${college.code}?tab=Overview`}
                    className="rounded-lg bg-counsly-soft/40 border border-counsly-line p-2.5 flex flex-col justify-between transition duration-200 hover:border-counsly-coral hover:bg-counsly-soft"
                  >
                    <span className="text-counsly-muted font-medium">Seats</span>
                    <strong className="font-mono text-sm font-semibold text-counsly-ink mt-0.5">{college.seats}</strong>
                  </Link>
                  <Link 
                    href={`/explore/${college.code}?tab=Fees & Facilities`}
                    className="rounded-lg bg-counsly-soft/40 border border-counsly-line p-2.5 flex flex-col justify-between transition duration-200 hover:border-counsly-coral hover:bg-counsly-soft"
                  >
                    <span className="text-counsly-muted font-medium">Hostel</span>
                    <strong className="text-sm font-semibold text-counsly-ink mt-0.5">{college.hostel ? "Yes" : "No"}</strong>
                  </Link>
                  <Link 
                    href={`/explore/${college.code}?tab=Overview`}
                    className="rounded-lg bg-counsly-soft/40 border border-counsly-line p-2.5 flex flex-col justify-between transition duration-200 hover:border-counsly-coral hover:bg-counsly-soft"
                  >
                    <span className="text-counsly-muted font-medium">NBA</span>
                    <strong className="text-sm font-semibold text-counsly-ink mt-0.5">{college.nba ? "Yes" : "No"}</strong>
                  </Link>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-counsly-line/80">
                <Link className="button-primary flex-1 justify-center sm:flex-initial" href={`/explore/${college.code}`}>
                  College insight <ArrowRight className="h-4 w-4" />
                </Link>
                <Link className="button-secondary flex-1 justify-center sm:flex-initial" href={`/compare?ids=${college.code},2006`}>
                  Compare
                </Link>
              </div>
            </Surface>
          ))}
        </div>
      )}
    </div>
  );
}
