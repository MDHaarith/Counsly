"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiClient, postJson } from "@/lib/api";

interface BranchInsight {
  branch_code: string;
  branch_name: string;
  total_seats: number | null;
}

interface CollegeDetail {
  college_code: string;
  college_name: string;
  district: string | null;
  autonomous_status: string | null;
  hostel_boys: boolean | null;
  hostel_girls: boolean | null;
  transport_facilities: boolean | null;
  address: string | null;
  website: string | null;
  email: string | null;
  branches: BranchInsight[];
}

export default function CollegeDetailPage() {
  const params = useParams<{ code: string }>();
  const [detail, setDetail] = useState<CollegeDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null);

  useEffect(() => {
    apiClient<CollegeDetail>(`/api/explore/${params.code}`).then(setDetail).catch((err) => setError(err instanceof Error ? err.message : "Could not load college."));
  }, [params.code]);

  async function add(branch: BranchInsight) {
    setAdding(branch.branch_code);
    try {
      await postJson("/api/choices", { college_code: params.code, branch_code: branch.branch_code });
    } finally {
      setAdding(null);
    }
  }

  return (
    <div className="space-y-4 p-5">
      {error && <Card><p className="text-sm text-error-crimson">{error}</p></Card>}
      {!detail && !error && <p className="text-sm text-olive-gray">Loading college...</p>}
      {detail && (
        <>
          <div>
            <p className="text-sm font-medium text-olive-gray">{detail.college_code} · {detail.district ?? "District pending"}</p>
            <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">{detail.college_name}</h1>
          </div>
          <Card>
            <div className="flex flex-wrap gap-2">
              {detail.autonomous_status && <Badge>{detail.autonomous_status}</Badge>}
              {detail.hostel_boys && <Badge>boys hostel</Badge>}
              {detail.hostel_girls && <Badge>girls hostel</Badge>}
              {detail.transport_facilities && <Badge>transport</Badge>}
            </div>
            {detail.address && <p className="mt-3 text-sm leading-relaxed text-olive-gray">{detail.address}</p>}
          </Card>
          <div className="space-y-3">
            <h2 className="font-serif text-xl font-medium">Branches</h2>
            {detail.branches.map((branch) => (
              <Card key={branch.branch_code}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-serif text-lg font-medium">{branch.branch_name}</h3>
                    <p className="mt-1 font-mono text-sm text-stone-gray">{branch.branch_code} · {branch.total_seats ?? "-"} seats</p>
                  </div>
                  <Button variant="secondary" className="w-auto" onClick={() => add(branch)} disabled={adding === branch.branch_code}>{adding === branch.branch_code ? "Adding" : "Add"}</Button>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
