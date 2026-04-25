"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { apiClient } from "@/lib/api";

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

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfilePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient<ProfilePayload>("/api/profile").then(setProfile).catch((err) => setError(err instanceof Error ? err.message : "Could not load profile."));
  }, []);

  async function logout() {
    await apiClient("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  }

  return (
    <div className="space-y-4 p-5">
      <div>
        <p className="text-sm font-medium text-olive-gray">Profile</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">Student details</h1>
      </div>
      {error && <Card><p className="text-sm text-error-crimson">{error}</p></Card>}
      {!profile && !error && <div className="grid gap-3"><Skeleton className="h-28" /><Skeleton className="h-24" /></div>}
      {profile && (
        <>
          <Card variant="featured">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-serif text-xl font-medium">{profile.full_name ?? "Name not added"}</h2>
                <p className="mt-1 text-sm text-olive-gray">{profile.community_quota ?? "Community pending"} · {profile.home_district ?? "District pending"}</p>
              </div>
              {profile.paid ? <Badge variant="safe">Full Access</Badge> : <Badge>Free</Badge>}
            </div>
          </Card>
          <Card>
            <h2 className="font-serif text-lg font-medium">Marks</h2>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <p>Maths <span className="font-mono">{profile.maths_mark ?? "-"}</span></p>
              <p>Physics <span className="font-mono">{profile.physics_mark ?? "-"}</span></p>
              <p>Chemistry <span className="font-mono">{profile.chemistry_mark ?? "-"}</span></p>
              <p>Cutoff <span className="font-mono">{profile.cutoff_mark ?? "-"}</span></p>
            </div>
          </Card>
          <Button variant="secondary" onClick={logout}>Log out</Button>
          {!profile.paid && <Link href="/subscribe?from=profile"><Button>Unlock Full Access</Button></Link>}
        </>
      )}
    </div>
  );
}
