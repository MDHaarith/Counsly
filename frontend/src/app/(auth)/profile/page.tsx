import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ProfileClient } from "@/components/profile/ProfileClient";
import { getServerApi, redirectToLoginOnUnauthorized } from "@/lib/serverApi";

interface ProfilePayload {
  full_name: string | null;
  board: string | null;
  district: string | null;
  home_district: string | null;
  community_quota: string | null;
  maths_mark: number | null;
  physics_mark: number | null;
  chemistry_mark: number | null;
  cutoff_mark: number | null;
  official_rank: number | null;
  paid: boolean;
}

export default async function ProfilePage() {
  let profile: ProfilePayload | null = null;
  let error: string | null = null;

  try {
    profile = await getServerApi<ProfilePayload>("/api/profile");
  } catch (err) {
    redirectToLoginOnUnauthorized(err, "/profile");
    error = err instanceof Error ? err.message : "Could not load profile.";
  }

  return (
    <div className="space-y-4">
      <h1 className="font-serif text-3xl font-medium leading-tight">Student details</h1>

      {error && (
        <Card>
          <p className="text-sm text-error-crimson">{error}</p>
        </Card>
      )}

      {profile && (
        <>
          <Card variant="featured">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-serif text-xl font-medium">{profile.full_name ?? "Name not added"}</h2>
                <p className="mt-1 text-sm text-olive-gray">
                  {profile.community_quota ?? "Community pending"} · {profile.home_district ?? "District pending"}
                </p>
              </div>
              {profile.paid ? <Badge variant="safe">Full Access</Badge> : <Badge>Free</Badge>}
            </div>
          </Card>
          <Card>
            <h2 className="font-serif text-lg font-medium">Marks</h2>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <p>
                Maths <span className="font-mono">{profile.maths_mark ?? "-"}</span>
              </p>
              <p>
                Physics <span className="font-mono">{profile.physics_mark ?? "-"}</span>
              </p>
              <p>
                Chemistry <span className="font-mono">{profile.chemistry_mark ?? "-"}</span>
              </p>
              <p>
                Cutoff <span className="font-mono">{profile.cutoff_mark ?? "-"}</span>
              </p>
            </div>
          </Card>

          {/* Analytics section */}
          <details className="group">
            <summary className="cursor-pointer list-none">
              <Card>
                <div className="flex items-center justify-between">
                  <h2 className="font-serif text-lg font-medium">Your Stats</h2>
                  <span className="text-sm text-olive-gray transition-transform group-open:rotate-180">▼</span>
                </div>
              </Card>
            </summary>
            <Card className="mt-2">
              <div className="space-y-3 text-sm">
                {profile.cutoff_mark != null && (
                  <div>
                    <p className="text-olive-gray">Cutoff breakdown</p>
                    <p className="mt-1 font-mono">
                      {profile.maths_mark ?? "—"} + {profile.physics_mark != null ? `${profile.physics_mark}/2` : "—"} + {profile.chemistry_mark != null ? `${profile.chemistry_mark}/2` : "—"} ={" "}
                      <span className="font-semibold text-terracotta">{profile.cutoff_mark}</span>
                    </p>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-olive-gray">Community</p>
                    <p className="mt-0.5 font-medium">{profile.community_quota ?? "Not set"}</p>
                  </div>
                  <div>
                    <p className="text-olive-gray">District</p>
                    <p className="mt-0.5 font-medium">{profile.home_district ?? "Not set"}</p>
                  </div>
                </div>
                {profile.official_rank != null && (
                  <div>
                    <p className="text-olive-gray">Official TNEA rank</p>
                    <p className="mt-0.5 font-mono font-semibold">{profile.official_rank}</p>
                  </div>
                )}
                {profile.official_rank == null && (
                  <p className="text-stone-gray">Official rank not available yet</p>
                )}
              </div>
            </Card>
          </details>

          <ProfileClient isPaid={profile.paid} />
        </>
      )}
    </div>
  );
}
