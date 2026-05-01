import { RecommendationsClient } from "@/components/recommendations/RecommendationsClient";
import { getServerApi, redirectToLoginOnUnauthorized } from "@/lib/serverApi";

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
  let initialData: RecommendationsPayload | null = null;
  let error: string | null = null;

  try {
    initialData = await getServerApi<RecommendationsPayload>("/api/recommendations");
  } catch (err) {
    redirectToLoginOnUnauthorized(err, "/recommendations");
    error = err instanceof Error ? err.message : "Could not load recommendations.";
  }

  return (
    <div className="space-y-4">
      <h1 className="font-serif text-3xl font-medium leading-tight">College matches</h1>

      {error && (
        <div className="rounded-xl border border-error-crimson/20 bg-error-crimson/5 p-4 text-sm text-error-crimson">
          {error}
        </div>
      )}

      <RecommendationsClient initialData={initialData} />
    </div>
  );
}
