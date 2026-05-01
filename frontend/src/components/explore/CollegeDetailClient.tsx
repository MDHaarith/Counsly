"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { postJson } from "@/lib/api";

interface BranchInsight {
  branch_code: string;
  branch_name: string;
  total_seats: number | null;
}

export function CollegeDetailClient({ branches, collegeCode }: { branches: BranchInsight[], collegeCode: string }) {
  const [adding, setAdding] = useState<string | null>(null);

  async function add(branch: BranchInsight) {
    setAdding(branch.branch_code);
    try {
      await postJson("/api/choices", { college_code: collegeCode, branch_code: branch.branch_code });
    } catch (err) {
      console.error("Failed to add choice", err);
    } finally {
      setAdding(null);
    }
  }

  return (
    <div className="space-y-3">
      <h2 className="font-serif text-xl font-medium">Branches</h2>
      {branches.map((branch) => (
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
        </Card>
      ))}
    </div>
  );
}
