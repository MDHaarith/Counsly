import { cookies } from "next/headers";

import { RecommendationsClient } from "@/components/recommendations/RecommendationsClient";
import { apiClient } from "@/lib/api";

const SESSION_COOKIE_NAME = process.env.NEXT_PUBLIC_SESSION_COOKIE_NAME ?? "counsly_session";

interface RecommendationItem {
  college_code: string;
  college_name: string;
  branch_code: string;
  branch_name: string;
  district: string | null;
  cutoff_rank: number | null;
  safety: "safe" | "moderate" | "ambitious" | null;
  season_year: number | null;
}

interface RecommendationsPayload {
  items: RecommendationItem[];
  total: number;
  returned: number;
  paid: boolean;
  restriction: "plan_limit" | "data_not_ready" | "ineligible" | null;
}

export default async function RecommendationsPage() {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);
  const headers: HeadersInit = sessionCookie ? { Cookie: `${SESSION_COOKIE_NAME}=${sessionCookie.value}` } : {};

  let initialData: RecommendationsPayload | null = null;
  let error: string | null = null;

  try {
    initialData = await apiClient<RecommendationsPayload>("/api/recommendations", { headers });
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load recommendations.";
  }

  return (
    <div className="space-y-4 p-5">
      <div>
        <p className="text-sm font-medium text-olive-gray">Recommendations</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">College matches</h1>
      </div>

      {error && (
        <div className="rounded-xl border border-error-crimson/20 bg-error-crimson/5 p-4 text-sm text-error-crimson">
          {error}
        </div>
      )}

      <RecommendationsClient initialData={initialData} />
    </div>
  );
}
