import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { CollegeDetailClient } from "@/components/explore/CollegeDetailClient";
import { getServerApi, redirectToLoginOnUnauthorized } from "@/lib/serverApi";

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

interface CollegeDetail {
  college_code: string;
  college_name: string;
  district: string | null;
  taluk: string | null;
  pincode: string | null;
  phone_fax: string | null;
  autonomous_status: string | null;
  minority_status: string | null;
  placement_record: string | null;
  hostel_boys: boolean | null;
  hostel_girls: boolean | null;
  hostel_boys_type: string | null;
  hostel_girls_type: string | null;
  transport_facilities: boolean | null;
  min_transport_charges: number | null;
  max_transport_charges: number | null;
  latitude: number | null;
  longitude: number | null;
  maps_url: string | null;
  address: string | null;
  website: string | null;
  email: string | null;
  nearest_railway_station: string | null;
  distance_from_railway_km: number | null;
  distance_from_dist_hq_km: number | null;
  dean_principal: string | null;
  anti_ragging_phone: string | null;
  type_of_mess: string | null;
  room_rent: string | null;
  branches: BranchInsight[];
  cutoffs: CutoffEntry[];
}

interface ProfilePayload {
  paid: boolean;
}

export default async function CollegeDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  let detail: CollegeDetail | null = null;
  let paid = false;
  let error: string | null = null;

  try {
    [detail, { paid }] = await Promise.all([
      getServerApi<CollegeDetail>(`/api/explore/${code}`),
      getServerApi<ProfilePayload>("/api/profile"),
    ]);
  } catch (err) {
    redirectToLoginOnUnauthorized(err, `/explore/${code}`);
    error = err instanceof Error ? err.message : "Could not load college.";
  }

  return (
    <div className="space-y-4">
      {error && (
        <Card>
          <p className="text-sm text-error-crimson">{error}</p>
        </Card>
      )}

      {detail && (
        <>
          {/* Header */}
          <div>
            <p className="text-sm font-medium text-olive-gray">
              {detail.college_code} · {detail.district ?? "District pending"}
              {detail.taluk ? ` · ${detail.taluk}` : ""}
            </p>
            <h1 className="mt-1 font-serif text-3xl font-medium leading-tight">{detail.college_name}</h1>
          </div>

          {/* Section 1: College Info (free) */}
          <Card>
            <div className="flex flex-wrap gap-2">
              {detail.autonomous_status && <Badge>{detail.autonomous_status}</Badge>}
              {detail.minority_status && detail.minority_status !== "No" && <Badge>{detail.minority_status}</Badge>}
              {detail.hostel_boys && <Badge>boys hostel{detail.hostel_boys_type ? ` (${detail.hostel_boys_type})` : ""}</Badge>}
              {detail.hostel_girls && <Badge>girls hostel{detail.hostel_girls_type ? ` (${detail.hostel_girls_type})` : ""}</Badge>}
              {detail.transport_facilities && <Badge>transport</Badge>}
              {detail.type_of_mess && <Badge>mess: {detail.type_of_mess}</Badge>}
            </div>
            {detail.address && <p className="mt-3 text-sm leading-relaxed text-olive-gray">{detail.address}</p>}
            {detail.pincode && <p className="mt-1 text-sm text-stone-gray">PIN: {detail.pincode}</p>}
            {detail.placement_record && (
              <p className="mt-2 text-sm font-medium text-anthracite">Placement: {detail.placement_record}</p>
            )}
          </Card>

          {/* Section 2: Contact (free) */}
          <Card>
            <h2 className="font-serif text-lg font-medium">Contact & Access</h2>
            <div className="mt-2 grid gap-1.5 text-sm text-olive-gray">
              {detail.dean_principal && <p>Dean/Principal: {detail.dean_principal}</p>}
              {detail.phone_fax && <p>Phone: {detail.phone_fax}</p>}
              {detail.email && (
                <p>
                  Email:{" "}
                  <a href={`mailto:${detail.email}`} className="text-terracotta underline">
                    {detail.email}
                  </a>
                </p>
              )}
              {detail.website && (
                <p>
                  Web:{" "}
                  <a href={detail.website} target="_blank" rel="noopener noreferrer" className="text-terracotta underline">
                    {detail.website}
                  </a>
                </p>
              )}
              {detail.nearest_railway_station && (
                <p>
                  Nearest railway: {detail.nearest_railway_station}
                  {detail.distance_from_railway_km ? ` (${detail.distance_from_railway_km} km)` : ""}
                </p>
              )}
              {detail.distance_from_dist_hq_km != null && (
                <p>Distance from district HQ: {detail.distance_from_dist_hq_km} km</p>
              )}
              {detail.anti_ragging_phone && detail.anti_ragging_phone !== "None" && (
                <p>Anti-ragging: {detail.anti_ragging_phone}</p>
              )}
              {detail.maps_url && (
                <a href={detail.maps_url} target="_blank" rel="noopener noreferrer" className="inline-block mt-1 text-terracotta underline">
                  Open in Maps →
                </a>
              )}
            </div>
          </Card>

          {/* Section 3: Facilities (free) */}
          {(detail.room_rent || detail.min_transport_charges != null) && (
            <Card>
              <h2 className="font-serif text-lg font-medium">Facilities & Charges</h2>
              <div className="mt-2 grid gap-1.5 text-sm text-olive-gray">
                {detail.room_rent && <p>Room rent: ₹{detail.room_rent}</p>}
                {detail.min_transport_charges != null && detail.max_transport_charges != null && (
                  <p>
                    Transport: ₹{detail.min_transport_charges}
                    {detail.max_transport_charges > detail.min_transport_charges ? ` – ₹${detail.max_transport_charges}` : ""}
                  </p>
                )}
              </div>
            </Card>
          )}

          {/* Section 4: Branches & Cutoffs (premium blur) */}
          <CollegeDetailClient
            branches={detail.branches}
            cutoffs={detail.cutoffs}
            collegeCode={code}
            paid={paid}
          />
        </>
      )}
    </div>
  );
}
