"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, GitCompareArrows, MapPinned, TrainFront } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, PremiumBoard, Surface } from "@/components/ui";
import { choiceWriteDestination } from "@/lib/access.mjs";
import { addChoice, fetchCollegeDetail } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { currency, getCollege, trendRows } from "@/lib/product";

const tabs = ["Overview", "Cutoffs", "Fees & Facilities", "Placements", "Nearby"] as const;

export default function CollegeInsightPage({ params }: { params: { code: string } }) {
  const preview = useMemo(() => getCollege(params.code), [params.code]);
  const { user } = useApp();
  const router = useRouter();
  const [college, setCollege] = useState<any>(preview);
  const [tab, setTab] = useState<(typeof tabs)[number]>("Overview");
  const [status, setStatus] = useState("Loading live college detail and community-safe branch data.");
  const [choiceStatus, setChoiceStatus] = useState("");

  useEffect(() => {
    let active = true;
    fetchCollegeDetail(params.code)
      .then((detail) => {
        if (!active) return;
        setCollege(detail);
        setStatus("Live college detail loaded from the workspace API.");
      })
      .catch(() => {
        if (!active) return;
        setCollege(preview);
        setStatus(preview ? "API detail unavailable. Preview evidence remains visible." : "College detail could not be loaded.");
      });

    return () => {
      active = false;
    };
  }, [params.code, preview]);

  if (!college) {
    return (
      <Surface className="space-y-4 p-6" tone="paper">
        <p className="eyebrow">College insight</p>
        <h1 className="font-display text-4xl text-counsly-ink">No detail found for {params.code}.</h1>
        <Link className="button-primary" href="/explore">Return to explorer</Link>
      </Surface>
    );
  }

  const cutoffRows = college.cutoffTrends?.[college.branchCode] ?? [];
  const branches = college.branches ?? [];

  return (
    <div className="space-y-6">
      <Link className="button-quiet w-fit" href="/explore">
        <ArrowLeft className="h-4 w-4" /> Back to explorer
      </Link>
      <PageHeader
        actions={
          <>
            <button
              className="button-primary"
              onClick={async () => {
                const destination = choiceWriteDestination(user, "explore");
                if (destination) {
                  router.push(destination);
                  return;
                }
                try {
                  await addChoice({ ...college, notes: "Added from college insight." });
                  trackFunnelEvent("college_added", {
                    branch_code: college.branchCode,
                    college_code: college.code,
                    feature: "explore",
                    user,
                  });
                  setChoiceStatus(`${college.code} ${college.branchCode} added to the primary choice list.`);
                } catch {
                  setChoiceStatus("Add-to-choice needs a reachable workspace API. Branch actions remain below.");
                }
              }}
              type="button"
            >
              Add branch
            </button>
            <Link className="button-secondary" href={`/compare?ids=${college.code},2006`}>
              <GitCompareArrows className="h-4 w-4" /> Compare
            </Link>
          </>
        }
        description={`${college.branchName} decision page with live branches, cutoff evidence, facility context, and shortlist actions.`}
        eyebrow={`${college.type} college in ${college.district}`}
        title={college.name}
      />

      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{choiceStatus || status}</p>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Cutoff", college.cutoff ? college.cutoff.toFixed(2) : "Trend view"],
          ["Annual fees", college.fees ? currency(college.fees) : "Pending"],
          ["Placement", college.placementRate ? `${college.placementRate}%` : "Pending"],
          ["Average package", college.averagePackage ? `${college.averagePackage} LPA` : "Pending"],
        ].map(([label, value]) => (
          <Surface className="space-y-2 p-4" key={label} tone="paper">
            <p className="eyebrow">{label}</p>
            <p className="font-mono text-2xl text-counsly-ink">{value}</p>
          </Surface>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_420px]">
        <Surface className="space-y-5 p-6" tone="paper">
          <div className="flex flex-wrap gap-2">
            {tabs.map((item) => (
              <button key={item} onClick={() => setTab(item)} type="button">
                <Badge tone={tab === item ? "coral" : "neutral"}>{item}</Badge>
              </button>
            ))}
          </div>

          {tab === "Overview" && (
            <div className="space-y-4">
              <h2 className="font-display text-3xl text-counsly-ink">Decision overview</h2>
              <p className="text-sm leading-7 text-counsly-body">
                {college.address || "Address context is still being reconciled."} Use the tabs to inspect branch intake,
                cutoff movement, live facilities, and nearby travel context before fixing its priority.
              </p>
              <div className="grid gap-3 md:grid-cols-2">
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Accreditation</p>
                  <p className="mt-2 text-sm leading-6 text-counsly-body">
                    {college.autonomous ? "Autonomous" : "Affiliated"} institution with {college.nba ? "NBA" : "no listed NBA"} signal.
                  </p>
                </article>
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Branch preview</p>
                  <p className="mt-2 text-sm leading-6 text-counsly-body">
                    {branches.length || 1} branch surface{branches.length === 1 ? "" : "s"} available for choice analysis.
                  </p>
                </article>
              </div>
            </div>
          )}

          {tab === "Cutoffs" && (
            <div className="space-y-3">
              <h2 className="font-display text-3xl text-counsly-ink">Branch cutoff trend</h2>
              {(cutoffRows.length ? cutoffRows : trendRows.slice(1)).map((row: any) => (
                <div className="grid grid-cols-[70px_1fr_auto] items-center gap-3 rounded-lg bg-counsly-soft p-3" key={row.year}>
                  <span className="font-mono text-sm text-counsly-muted">{row.year}</span>
                  <span className="text-sm text-counsly-body">{college.branchCode} cutoff movement</span>
                  <strong className="font-mono text-counsly-ink">{row.cutoff_mark ?? row.ambitious}</strong>
                </div>
              ))}
              {(branches.length ? branches : [{ code: college.branchCode, name: college.branchName, approved_intake: college.seats }]).map((branch: any) => {
                const trends = college.cutoffTrends?.[branch.code] ?? [];
                const direction = trends.length > 1 && trends[0].cutoff_mark > trends[trends.length - 1].cutoff_mark ? "rising" : trends.length > 1 ? "stable" : "preview";
                return (
                  <details className="rounded-lg border border-counsly-line p-4" key={`cutoff-${branch.code}`}>
                    <summary className="cursor-pointer text-sm font-medium text-counsly-ink">
                      {branch.code} {branch.name} branch insight
                    </summary>
                    <div className="mt-3 grid gap-2 text-sm text-counsly-body sm:grid-cols-3">
                      <p className="rounded-md bg-counsly-soft p-3">Community seats <strong className="block font-mono">{branch.seats?.total || branch.approved_intake || 0}</strong></p>
                      <p className="rounded-md bg-counsly-soft p-3">Trend <strong className="block">{direction}</strong></p>
                      <p className="rounded-md bg-counsly-soft p-3">Last cutoff rank <strong className="block font-mono">{trends[0]?.cutoff_rank || college.cutoffRank || "Pending"}</strong></p>
                    </div>
                    <button
                      className="button-secondary mt-3"
                      onClick={async () => {
                        const destination = choiceWriteDestination(user, "explore");
                        if (destination) {
                          router.push(destination);
                          return;
                        }
                        try {
                          await addChoice({ ...college, branchCode: branch.code, branchName: branch.name, notes: "Branch chosen from cutoff insight." });
                          trackFunnelEvent("college_added", {
                            branch_code: branch.code,
                            college_code: college.code,
                            feature: "explore_cutoff",
                            user,
                          });
                          setChoiceStatus(`${college.code} ${branch.code} added from cutoff insight.`);
                        } catch {
                          setChoiceStatus("Branch add could not reach the workspace API.");
                        }
                      }}
                      type="button"
                    >
                      Add {branch.code} to choices
                    </button>
                  </details>
                );
              })}
            </div>
          )}

          {tab === "Fees & Facilities" && (
            <div className="grid gap-3 md:grid-cols-2">
              <article className="rounded-lg border border-counsly-line p-4">
                <p className="eyebrow">Annual fees</p>
                <p className="mt-2 font-mono text-xl text-counsly-ink">{college.fees ? currency(college.fees) : "Pending"}</p>
              </article>
              <article className="rounded-lg border border-counsly-line p-4">
                <p className="eyebrow">Hostel</p>
                <p className="mt-2 text-sm leading-6 text-counsly-body">{college.hostel ? "Available" : "Not listed"}. Monthly cost and caution deposit show when source data is audited.</p>
              </article>
              <article className="rounded-lg border border-counsly-line p-4">
                <p className="eyebrow">Transport</p>
                <p className="mt-2 text-sm leading-6 text-counsly-body">{college.transport ? "Available" : "Not listed"} in the current data surface.</p>
              </article>
              <article className="rounded-lg border border-counsly-line p-4">
                <p className="eyebrow">Establishment fees</p>
                <p className="mt-2 text-sm leading-6 text-counsly-body">Pending verified source row.</p>
              </article>
            </div>
          )}

          {tab === "Placements" && (
            <div className="space-y-3">
              <h2 className="font-display text-3xl text-counsly-ink">Placement evidence</h2>
              <div className={user?.subscription_active ? "grid gap-3 md:grid-cols-2" : "relative grid gap-3 md:grid-cols-2"}>
                {!user?.subscription_active && <div className="absolute inset-0 z-10 rounded-xl bg-counsly-canvas/70 backdrop-blur-[3px]" />}
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Placement rate</p>
                  <p className="mt-2 font-mono text-xl text-counsly-ink">{college.placementRate || "-"}%</p>
                </article>
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Average package</p>
                  <p className="mt-2 font-mono text-xl text-counsly-ink">{college.averagePackage || "-"} LPA</p>
                </article>
              </div>
              {!user?.subscription_active && <PremiumBoard body="Placement rows unlock with Full Access while free insight keeps the decision structure visible." title="Placement evidence is a paid detail" />}
            </div>
          )}

          {tab === "Nearby" && (
            <div className="space-y-3">
              <h2 className="font-display text-3xl text-counsly-ink">Nearby and map context</h2>
              <div className="rounded-xl border border-counsly-line bg-[radial-gradient(circle_at_20%_20%,rgba(204,120,92,0.28),transparent_36%),linear-gradient(135deg,#efe9de,#faf9f5)] p-5">
                <p className="flex gap-2 text-sm leading-6 text-counsly-body">
                  <MapPinned className="mt-1 h-4 w-4 shrink-0 text-counsly-coral" />
                  {college.latitude && college.longitude
                    ? `Map pin ready at ${college.latitude.toFixed(3)}, ${college.longitude.toFixed(3)}.`
                    : "Map coordinates are not listed yet; use travel evidence below."}
                </p>
              </div>
              <div className="rounded-xl border border-counsly-line p-4 text-sm leading-6 text-counsly-body">
                <p className="eyebrow">Nearest TFC</p>
                {college.nearestTfc ? (
                  <p className="mt-2">{college.nearestTfc.centre_name}, {college.nearestTfc.district}. {college.nearestTfc.address} {college.nearestTfc.phone}</p>
                ) : (
                  <p className="mt-2">TFC context appears from the student district when seeded in the workspace API.</p>
                )}
              </div>
            </div>
          )}
        </Surface>

        <div className="space-y-4">
          <Surface className="space-y-4 p-6" tone="dark">
            <h2 className="font-display text-3xl text-white">Nearby</h2>
            <p className="flex gap-2 text-sm leading-6 text-counsly-card">
              <TrainFront className="mt-1 h-4 w-4 shrink-0 text-counsly-coral" />
              {college.railway}, {college.distanceKm || "distance pending"} km away.
            </p>
            <p className="flex gap-2 text-sm leading-6 text-counsly-card">
              <MapPinned className="mt-1 h-4 w-4 shrink-0 text-counsly-teal" />
              {college.website ? "Official website is listed for this detail row." : "Nearest TFC panel becomes district-specific after onboarding."}
            </p>
          </Surface>
          <PremiumBoard
            body="Placement detail and community seat evidence stay structurally visible, while masked premium rows keep free comparisons honest."
            title="Full college insight"
          />
        </div>
      </div>
    </div>
  );
}
