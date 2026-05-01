import { CollegeSearch } from "@/components/explore/CollegeSearch";
import { getServerApi, redirectToLoginOnUnauthorized } from "@/lib/serverApi";

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

export default async function ExplorePage() {
  let initialData: ExplorePayload | null = null;
  try {
    initialData = await getServerApi<ExplorePayload>("/api/explore");
  } catch (err) {
    redirectToLoginOnUnauthorized(err, "/explore");
    console.error("Failed to fetch initial explore data", err);
  }

  return (
    <div className="space-y-4">
      <h1 className="font-serif text-3xl font-medium leading-tight">College directory</h1>
      <CollegeSearch initialData={initialData} />
    </div>
  );
}
