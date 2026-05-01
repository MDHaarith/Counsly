"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { postJson } from "@/lib/api";

interface BranchInsight {
  branch_code: string;
  branch_name: string;
  total_seats: number | null;
}

interface CutoffEntry {
  branch_code: string;
  community_quota: string;
  closing_rank: number | null;
  closing_mark: number | null;
  season_year: number | null;
  round_number: number | null;
}

interface Props {
  branches: BranchInsight[];
  cutoffs: CutoffEntry[];
  collegeCode: string;
  paid: boolean;
}

export function CollegeDetailClient({ branches, cutoffs, collegeCode, paid }: Props) {
  const [adding, setAdding] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function add(branch: BranchInsight) {
    setAdding(branch.branch_code);
    setError(null);
    try {
      await postJson("/api/choices", { college_code: collegeCode, branch_code: branch.branch_code });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add to choices.");
    } finally {
      setAdding(null);
    }
  }

  // Group cutoffs by branch_code for easy lookup
  const cutoffsByBranch: Record<string, CutoffEntry[]> = {};
  for (const c of cutoffs) {
    if (!cutoffsByBranch[c.branch_code]) cutoffsByBranch[c.branch_code] = [];
    cutoffsByBranch[c.branch_code].push(c);
  }

  return (
    <div className="space-y-3">
      {error && <p className="rounded-xl bg-error-crimson/10 px-4 py-2 text-sm text-error-crimson">{error}</p>}
      <h2 className="font-serif text-xl font-medium">Branches</h2>
      {branches.map((branch) => {
        const branchCutoffs = cutoffsByBranch[branch.branch_code] ?? [];
        return (
          <Card key={branch.branch_code}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-serif text-lg font-medium">{branch.branch_name}</h3>
                <p className="mt-1 font-mono text-sm text-stone-gray">
                  {branch.branch_code} · {branch.total_seats ?? "-"} seats
                </p>
              </div>
              <Button
                variant="secondary"
                className="w-auto"
                onClick={() => add(branch)}
                disabled={adding === branch.branch_code}
              >
                {adding === branch.branch_code ? "Adding" : "Add"}
              </Button>
            </div>

            {/* Cutoff section — blurred for free users */}
            {branchCutoffs.length > 0 && (
              <div className="relative mt-3">
                <div className={!paid ? "select-none blur-[4px]" : ""}>
                  <div className="grid gap-1.5">
                    {branchCutoffs.slice(0, 4).map((c, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg bg-warm-sand/30 px-3 py-1.5 text-sm">
                        <span className="font-medium text-anthracite">
                          {c.community_quota}
                          {c.season_year ? ` ${c.season_year}` : ""}
                          {c.round_number ? ` R${c.round_number}` : ""}
                        </span>
                        <span className="font-mono text-xs text-olive-gray">
                          {c.closing_rank ? `Rank ${c.closing_rank}` : ""}
                          {c.closing_mark ? ` · ${c.closing_mark}` : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                {!paid && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Badge variant="safe">🔒 Unlock cutoff data</Badge>
                  </div>
                )}
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}
