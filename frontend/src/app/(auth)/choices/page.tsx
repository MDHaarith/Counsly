import { ChoicesClient } from "@/components/choices/ChoicesClient";
import { getServerApi, redirectToLoginOnUnauthorized } from "@/lib/serverApi";

interface ChoiceItem {
  id: string;
  priority: number;
  college_code: string;
  college_name: string | null;
  branch_code: string;
  branch_name: string | null;
  district: string | null;
  system_category: "safe" | "moderate" | "ambitious" | null;
  manual_category: "safe" | "moderate" | "ambitious" | null;
  notes: string | null;
}

interface ChoicesPayload {
  items: ChoiceItem[];
  limit: number;
  paid: boolean;
}

export default async function ChoicesPage() {
  let initialData: ChoicesPayload | null = null;
  let error: string | null = null;

  try {
    initialData = await getServerApi<ChoicesPayload>("/api/choices");
  } catch (err) {
    redirectToLoginOnUnauthorized(err, "/choices");
    error = err instanceof Error ? err.message : "Could not load choices.";
  }

  return (
    <div className="space-y-4 p-5">
      <div>
        <p className="text-sm font-medium text-olive-gray">Choice filing</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">Your ordered list</h1>
        {initialData && (
          <p className="mt-2 text-sm text-olive-gray">
            {initialData.items.length}/{initialData.limit} active rows · tap a priority number to move.
          </p>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-error-crimson/20 bg-error-crimson/5 p-4 text-sm text-error-crimson">
          {error}
        </div>
      )}

      <ChoicesClient initialData={initialData} />
    </div>
  );
}
