"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
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

export function CollegeSearch({ initialData }: { initialData: ExplorePayload | null }) {
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [districts, setDistricts] = useState<string[]>([]);
  const [data, setData] = useState<ExplorePayload | null>(initialData);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiClient<{ districts: string[] }>("/api/explore/districts")
      .then((res) => setDistricts(res.districts))
      .catch(() => {});
  }, []);

  async function search(overrideDistrict?: string) {
    setLoading(true);
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    const d = overrideDistrict ?? district;
    if (d) params.set("district", d);
    const qs = params.toString() ? `?${params.toString()}` : "";
    try {
      setData(await apiClient<ExplorePayload>(`/api/explore${qs}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load colleges.");
    } finally {
      setLoading(false);
    }
  }

  function handleDistrictChange(value: string) {
    setDistrict(value);
    search(value);
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="College name or code"
          className="flex-1"
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <Button variant="secondary" className="w-auto" onClick={() => search()} disabled={loading}>
          {loading ? "..." : "Search"}
        </Button>
      </div>

      {districts.length > 0 && (
        <select
          value={district}
          onChange={(e) => handleDistrictChange(e.target.value)}
          className="w-full rounded-xl border border-warm-sand bg-white px-3 py-2.5 text-sm text-anthracite outline-none focus:border-terracotta"
        >
          <option value="">All districts</option>
          {districts.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      )}

      {error && (
        <Card>
          <p className="text-sm text-error-crimson">{error}</p>
        </Card>
      )}

      {loading && (
        <div className="grid gap-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      )}

      {!loading && data && (
        <>
          <p className="text-sm text-stone-gray">
            Showing {data.items.length} of {data.total}
          </p>
          <div className="grid gap-3">
            {data.items.map((college) => (
              <Link key={college.college_code} href={`/explore/${college.college_code}`}>
                <Card>
                  <h2 className="font-serif text-lg font-medium leading-snug">{college.college_name}</h2>
                  <p className="mt-1 text-sm text-olive-gray">
                    {college.college_code} · {college.district ?? "District pending"}
                  </p>
                  <p className="mt-2 text-xs text-stone-gray">{college.autonomous_status ?? "Autonomy pending"}</p>
                </Card>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
