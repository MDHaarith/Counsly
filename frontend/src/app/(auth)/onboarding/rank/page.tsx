"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { apiClient } from "@/lib/api";

interface RankBand {
  rank_min: number | null;
  rank_max: number | null;
  confidence_label: "High" | "Medium" | "Low" | null;
  sample_size: number | null;
  source_years: number[];
  is_abstain: boolean;
  disclaimer: string;
}

export default function RankPage() {
  const [rank, setRank] = useState<RankBand | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient<RankBand>("/api/onboarding/rank").then(setRank).catch((err) => setError(err instanceof Error ? err.message : "Rank guidance is not ready."));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-serif text-3xl font-medium leading-tight">Rank band</h1>
        <p className="mt-2 text-sm leading-relaxed text-olive-gray">This is range guidance from available TNEA data. Official TNEA rank replaces it when released.</p>
      </div>
      <Card variant="featured">
        {!rank && !error && <Skeleton className="h-24" />}
        {error && <p className="text-sm text-error-crimson">{error}</p>}
        {rank && rank.is_abstain && <p className="text-sm leading-relaxed text-olive-gray">Not enough historical data to estimate a reliable range for this marks combination.</p>}
        {rank && !rank.is_abstain && (
          <div>
            <p className="text-sm text-olive-gray">Estimated range</p>
            <p className="mt-2 font-mono text-4xl font-semibold leading-none">
              {rank.rank_min ?? "—"} – {rank.rank_max ?? "—"}
            </p>
            <div className="mt-4 flex items-center gap-2">
              <Badge>{rank.confidence_label ?? "Unknown"} confidence</Badge>
              <Badge>Historical range</Badge>
              <span className="text-xs text-stone-gray">{rank.sample_size ?? 0} samples</span>
            </div>
          </div>
        )}
        {rank && <p className="mt-4 text-xs leading-relaxed text-stone-gray">{rank.disclaimer}</p>}
      </Card>
      <Link href="/dashboard"><Button>Go to dashboard</Button></Link>
    </div>
  );
}
