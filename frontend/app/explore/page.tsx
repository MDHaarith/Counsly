"use client";

import { useDeferredValue, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";

import { Badge, PageHeader, Surface } from "@/components/ui";
import { searchColleges } from "@/lib/api.mjs";
import { branches, collegeCatalog, districts, toneForBand, cleanCollegeName } from "@/lib/product";

export default function ExplorePage() {
  const [search, setSearch] = useState("");
  const [district, setDistrict] = useState("");
  const [branch, setBranch] = useState("");
  const [sort, setSort] = useState<"fit" | "name" | "code">("fit");
  const [results, setResults] = useState(collegeCatalog);
  const [source, setSource] = useState("Preview catalog is ready while the live fit search loads.");
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
        setSource(rows.length ? "Live fit-ranked search loaded from the workspace API." : "No live matches. Preview catalog stays visible.");
      })
      .catch(() => {
        if (!active) return;
        setResults(collegeCatalog);
        setSource("API unavailable. Preview catalog keeps compare and college insight paths open.");
      });

    return () => {
      active = false;
    };
  }, [branch, deferredSearch, district]);

  return (
    <div className="space-y-6">
      <PageHeader
        description="Fit-ranked college browsing with branch, district, insight, shortlist, and compare context in one path."
        eyebrow="College explorer"
        title="Begin with colleges worth deciding on."
      />

      <Surface className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_190px_230px_180px]" tone="paper">
        <label className="field-label">
          Search college or code
          <span className="relative">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-counsly-muted" />
            <input className="field pl-10" onChange={(event) => setSearch(event.target.value)} placeholder="CEG, PSG, Chennai..." value={search} />
          </span>
        </label>
        <label className="field-label">
          District
          <select className="field" onChange={(event) => setDistrict(event.target.value)} value={district}>
            <option value="">All districts</option>
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
        <label className="field-label">
          Sort
          <select className="field" onChange={(event) => setSort(event.target.value as typeof sort)} value={sort}>
            <option value="fit">Fit ranked</option>
            <option value="name">Alphabetical</option>
            <option value="code">College code</option>
          </select>
        </label>
      </Surface>

      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{source}</p>

      <div className="grid gap-4 lg:grid-cols-2">
        {colleges.map((college) => (
          <Surface className="space-y-4 p-5" key={`${college.code}-${college.branchCode}`} tone="paper">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="mb-2 flex flex-wrap gap-2">
                  <Badge>{college.code}</Badge>
                  <Badge tone={toneForBand(college.fitBand)}>{college.fitBand} fit</Badge>
                </div>
                <h2 className="font-display text-3xl text-counsly-ink">{cleanCollegeName(college.name)}</h2>
                <p className="mt-1 text-sm leading-6 text-counsly-body">
                  {college.branchName} in {college.district}
                </p>
              </div>
              <p className="rounded-lg bg-counsly-soft px-3 py-2 font-mono text-sm text-counsly-ink">
                Fit {college.fitScore}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <span className="rounded-lg bg-counsly-soft p-3">Cutoff <strong className="block font-mono">{college.cutoff}</strong></span>
              <span className="rounded-lg bg-counsly-soft p-3">Seats <strong className="block font-mono">{college.seats}</strong></span>
              <span className="rounded-lg bg-counsly-soft p-3">Hostel <strong className="block">{college.hostel ? "Yes" : "No"}</strong></span>
              <span className="rounded-lg bg-counsly-soft p-3">NBA <strong className="block">{college.nba ? "Yes" : "No"}</strong></span>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link className="button-primary" href={`/explore/${college.code}`}>
                College insight <ArrowRight className="h-4 w-4" />
              </Link>
              <Link className="button-secondary" href={`/compare?ids=${college.code},2006`}>
                Compare
              </Link>
            </div>
          </Surface>
        ))}
      </div>
    </div>
  );
}
