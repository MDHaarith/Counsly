"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiClient } from "@/lib/api";

interface CollegeItem {
  college_code: string;
  college_name: string;
  district: string | null;
  autonomous_status: string | null;
  hostel_boys: boolean | null;
  hostel_girls: boolean | null;
  transport_facilities: boolean | null;
}

interface ExplorePayload {
  items: CollegeItem[];
  total: number;
}

export default function ExplorePage() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState<ExplorePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient<ExplorePayload>("/api/explore")
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load colleges."));
  }, []);

  async function search() {
    const params = query ? `?q=${encodeURIComponent(query)}` : "";
    try {
      setData(await apiClient<ExplorePayload>(`/api/explore${params}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load colleges.");
    }
  }

  return (
    <div className="space-y-4 p-5">
      <div>
        <p className="text-sm font-medium text-olive-gray">Explore</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">College directory</h1>
      </div>
      <div className="flex gap-2">
        <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="College name or code" className="flex-1" />
        <Button variant="secondary" className="w-auto" onClick={search}>Search</Button>
      </div>
      {error && <Card><p className="text-sm text-error-crimson">{error}</p></Card>}
      {!data && !error && <p className="text-sm text-olive-gray">Loading colleges...</p>}
      {data && <p className="text-sm text-stone-gray">Showing {data.items.length} of {data.total}</p>}
      <div className="grid gap-3">
        {data?.items.map((college) => (
          <Link key={college.college_code} href={`/explore/${college.college_code}`}>
            <Card>
              <h2 className="font-serif text-lg font-medium leading-snug">{college.college_name}</h2>
              <p className="mt-1 text-sm text-olive-gray">{college.college_code} · {college.district ?? "District pending"}</p>
              <p className="mt-2 text-xs text-stone-gray">{college.autonomous_status ?? "Autonomy pending"}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
