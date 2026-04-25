"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { apiClient, postJson } from "@/lib/api";
import type { SafetyLabel } from "@/types";

interface RecommendationItem {
  college_code: string;
  college_name: string;
  branch_code: string;
  branch_name: string;
  district: string | null;
  cutoff_rank: number | null;
  safety: SafetyLabel | null;
  season_year: number | null;
}

interface RecommendationsPayload {
  items: RecommendationItem[];
  total: number;
  returned: number;
  paid: boolean;
  restriction: "plan_limit" | "data_not_ready" | "ineligible" | null;
}

export default function RecommendationsPage() {
  const [data, setData] = useState<RecommendationsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null);

  useEffect(() => {
    apiClient<RecommendationsPayload>("/api/recommendations").then(setData).catch((err) => setError(err instanceof Error ? err.message : "Could not load recommendations."));
  }, []);

  async function add(item: RecommendationItem) {
    setAdding(`${item.college_code}-${item.branch_code}`);
    try {
      await postJson("/api/choices", { college_code: item.college_code, branch_code: item.branch_code });
    } finally {
      setAdding(null);
    }
  }

  return (
    <div className="space-y-4 p-5">
      <div>
        <p className="text-sm font-medium text-olive-gray">Recommendations</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">College matches</h1>
      </div>
      {error && <Card><p className="text-sm text-error-crimson">{error}</p></Card>}
      {!data && !error && <div className="grid gap-3"><Skeleton className="h-28" /><Skeleton className="h-28" /><Skeleton className="h-28" /></div>}
      {data?.restriction === "ineligible" && <Card><h2 className="font-serif text-lg font-medium">Recommendations locked</h2><p className="mt-1 text-sm leading-relaxed text-olive-gray">Your entered cutoff is below the guidance threshold, so Counsly will not show recommendation claims for this cycle.</p></Card>}
      {data?.restriction === "data_not_ready" && <Card><h2 className="font-serif text-lg font-medium">Data not ready</h2><p className="mt-1 text-sm leading-relaxed text-olive-gray">Verified cutoff data must be seeded before Counsly can recommend colleges.</p></Card>}
      {data && data.restriction === "plan_limit" && <Card variant="featured"><h2 className="font-serif text-lg font-medium">Showing {data.returned} of {data.total}</h2><p className="mt-1 text-sm text-olive-gray">Unlock all recommendations for this season.</p><Link href="/subscribe?from=recommendations"><Button className="mt-4">Unlock Full Access</Button></Link></Card>}
      <div className="grid gap-3">
        {data?.items.map((item) => (
          <Card key={`${item.college_code}-${item.branch_code}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-serif text-lg font-medium leading-snug">{item.college_name}</h2>
                <p className="mt-1 text-sm text-olive-gray">{item.branch_name} · {item.district ?? "District pending"}</p>
              </div>
              {item.safety && <Badge variant={item.safety}>{item.safety}</Badge>}
            </div>
            <div className="mt-3 flex items-center justify-between gap-3">
              <p className="font-mono text-sm text-stone-gray">Cutoff rank {item.cutoff_rank ?? "-"}</p>
              <Button variant="secondary" className="w-auto" onClick={() => add(item)} disabled={adding === `${item.college_code}-${item.branch_code}`}>{adding ? "Adding" : "Add"}</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
