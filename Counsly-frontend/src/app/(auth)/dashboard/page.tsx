"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { apiClient } from "@/lib/api";

interface StatusPayload {
  tnea_phase: number;
  total_rounds: number;
  round_dates: Array<{ round_number: number; date: string }>;
  data_freshness: Record<string, string>;
}

interface ProfilePayload {
  full_name: string | null;
  cutoff_mark: number | null;
  paid: boolean;
}

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [profile, setProfile] = useState<ProfilePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([apiClient<StatusPayload>("/api/config/status"), apiClient<ProfilePayload>("/api/profile")])
      .then(([statusData, profileData]) => {
        setStatus(statusData);
        setProfile(profileData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load dashboard."));
  }, []);

  const unverified = status ? Object.entries(status.data_freshness).filter(([, value]) => value !== "verified") : [];

  return (
    <div className="space-y-5 p-5">
      <div>
        <p className="text-sm font-medium text-olive-gray">Home</p>
        <h1 className="mt-1 font-serif text-[30px] font-medium leading-tight">{profile?.full_name ? `Hi, ${profile.full_name}` : "Your counselling dashboard"}</h1>
      </div>

      {error && <Card><p className="text-sm text-error-crimson">{error}</p><Link href="/login"><Button className="mt-4">Login again</Button></Link></Card>}

      {!status && !profile && !error && <div className="grid gap-3"><Skeleton className="h-32" /><Skeleton className="h-24" /></div>}

      {profile && <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-serif text-xl font-medium">Next best action</h2>
            <p className="mt-1 text-sm leading-relaxed text-olive-gray">{profile?.cutoff_mark ? "Review colleges matched to your current rank context." : "Complete onboarding so recommendations can use your marks and community."}</p>
          </div>
          {profile?.paid ? <Badge variant="safe">Paid</Badge> : <Badge>Free</Badge>}
        </div>
        <Link href={profile?.cutoff_mark ? "/recommendations" : "/onboarding/marks"}><Button className="mt-4">{profile?.cutoff_mark ? "View recommendations" : "Continue setup"}</Button></Link>
      </Card>}

      {status && status.round_dates.length > 0 && (
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="font-serif text-lg font-medium">TNEA rounds</h2>
              <p className="mt-1 text-sm text-olive-gray">{status.total_rounds} total rounds configured</p>
            </div>
            <Badge>{status.tnea_phase > 0 ? `Phase ${status.tnea_phase}` : "Schedule"}</Badge>
          </div>
          <div className="mt-3 grid gap-2">
            {status.round_dates.map((round) => (
              <div key={round.round_number} className="flex items-center justify-between gap-3 rounded-xl bg-warm-sand/45 px-3 py-2 text-sm">
                <span className="font-medium text-anthracite">Round {round.round_number}</span>
                <span className="text-right font-mono text-xs text-olive-gray">{round.date}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-3">
        <Link href="/choices"><Card><h3 className="font-serif text-lg font-medium">Choice list</h3><p className="mt-1 text-sm text-olive-gray">Add colleges, reorder priorities, and keep notes.</p></Card></Link>
        <Link href="/explore"><Card><h3 className="font-serif text-lg font-medium">Explore colleges</h3><p className="mt-1 text-sm text-olive-gray">Search the verified college master.</p></Card></Link>
      </div>

      {unverified.length > 0 && (
        <Card>
          <h2 className="font-serif text-lg font-medium">Data readiness</h2>
          <p className="mt-1 text-sm leading-relaxed text-olive-gray">Some datasets are not verified yet. Counsly will show data-not-ready states instead of decision claims.</p>
          <div className="mt-3 flex flex-wrap gap-2">{unverified.slice(0, 5).map(([key, value]) => <Badge key={key}>{key}: {value}</Badge>)}</div>
        </Card>
      )}
    </div>
  );
}
