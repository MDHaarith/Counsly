import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { CollegeDetailClient } from "@/components/explore/CollegeDetailClient";
import { getServerApi, redirectToLoginOnUnauthorized } from "@/lib/serverApi";

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

export default async function CollegeDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  let detail: CollegeDetail | null = null;
  let error: string | null = null;

  try {
    detail = await getServerApi<CollegeDetail>(`/api/explore/${code}`);
  } catch (err) {
    redirectToLoginOnUnauthorized(err, `/explore/${code}`);
    error = err instanceof Error ? err.message : "Could not load college.";
  }

  return (
    <div className="space-y-4 p-5">
      {error && (
        <Card>
          <p className="text-sm text-error-crimson">{error}</p>
        </Card>
      )}

      {detail && (
        <>
          <div>
            <p className="text-sm font-medium text-olive-gray">
              {detail.college_code} · {detail.district ?? "District pending"}
            </p>
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

          <CollegeDetailClient branches={detail.branches} collegeCode={code} />
        </>
      )}
    </div>
  );
}
