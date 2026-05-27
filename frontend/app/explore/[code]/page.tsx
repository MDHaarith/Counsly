"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, GitCompareArrows, MapPinned, TrainFront } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { choiceWriteDestination } from "@/lib/access.mjs";
import { addChoice, fetchCollegeDetail } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { currency, getCollege, trendRows, cleanCollegeName } from "@/lib/product";

const tabs = ["Overview", "Cutoffs", "Fees & Facilities", "Placements", "Nearby"] as const;

export default function CollegeInsightPage({ params }: { params: { code: string } }) {
  const preview = useMemo(() => getCollege(params.code), [params.code]);
  const { user } = useApp();
  const router = useRouter();
  const [college, setCollege] = useState<any>(preview);
  const [tab, setTab] = useState<(typeof tabs)[number]>("Overview");
  const [status, setStatus] = useState("Loading live college detail and community-safe branch data.");
  const [choiceStatus, setChoiceStatus] = useState("");

  const details = useMemo(() => {
    if (college?.detailsRaw) {
      try {
        return JSON.parse(college.detailsRaw);
      } catch (e) {
        return null;
      }
    }
    return null;
  }, [college?.detailsRaw]);

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
        title={cleanCollegeName(college.name)}
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

              {details && (
                <div className="grid gap-3 md:grid-cols-2 pt-2 border-t border-counsly-line">
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Administration & Location</p>
                    <div className="mt-2 text-sm leading-6 text-counsly-body space-y-1.5">
                      <p>Dean/Principal: <strong className="text-counsly-ink">{details.Dean_Principal || "N/A"}</strong></p>
                      <p>Anti-Ragging Help: <strong className="text-counsly-ink">{details.Anti_Ragging_Phone_No || "N/A"}</strong></p>
                      <p>Taluk / Region: <strong className="text-counsly-ink">{details.Taluk || "N/A"}</strong></p>
                      {details.Distance_in_KMS_from_Dist_HQ && (
                        <p>Distance from Dist HQ: <strong className="text-counsly-ink">{details.Distance_in_KMS_from_Dist_HQ} km</strong></p>
                      )}
                    </div>
                  </article>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Official Contacts & Banking</p>
                    <div className="mt-2 text-sm leading-6 text-counsly-body space-y-1.5">
                      <p>Email: <strong className="text-counsly-ink">{details["Email-ID"] || "N/A"}</strong></p>
                      <p>Phone/Fax: <strong className="text-counsly-ink">{details.Phone_Fax || "N/A"}</strong></p>
                      {details.Bank_Name && (
                        <p>Bank: <strong className="text-counsly-ink">{details.Bank_Name} {details.Bank_A_c_No ? `(A/c: ${details.Bank_A_c_No})` : ""}</strong></p>
                      )}
                      {details.Pincode && (
                        <p>Pincode: <strong className="text-counsly-ink">{details.Pincode}</strong></p>
                      )}
                    </div>
                  </article>
                </div>
              )}
            </div>
          )}

          {tab === "Cutoffs" && (
            <div className="space-y-3">
              <h2 className="font-display text-3xl text-counsly-ink">Branch cutoff trend</h2>
              {(cutoffRows.length ? cutoffRows : trendRows.slice(1)).map((row: { year: number | string; cutoff_mark?: number; ambitious?: number }) => (
                <div className="grid grid-cols-[70px_1fr_auto] items-center gap-3 rounded-lg bg-counsly-soft p-3" key={row.year}>
                  <span className="font-mono text-sm text-counsly-muted">{row.year}</span>
                  <span className="text-sm text-counsly-body">{college.branchCode} cutoff movement</span>
                  <strong className="font-mono text-counsly-ink">{row.cutoff_mark ?? row.ambitious}</strong>
                </div>
              ))}
              {(branches.length ? branches : [{ code: college.branchCode, name: college.branchName, approved_intake: college.seats }]).map((branch: { code: string; name: string; seats?: { total?: number }; approved_intake?: number }) => {
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
                <p className="eyebrow">Annual tuition fees</p>
                <p className="mt-2 font-mono text-xl text-counsly-ink">{college.fees ? currency(college.fees) : "Pending"}</p>
              </article>
              
              {details ? (
                <>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Boys Hostel Status</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">
                      Accommodation: <strong className="text-counsly-ink">{details.Hostel_Boys_Permanent_or_Rental || "Not Available"}</strong>
                      {details.Type_of_Mess && details.Type_of_Mess !== "-" && (
                        <span><br/>Mess Food Type: <strong className="text-counsly-ink">{details.Type_of_Mess}</strong></span>
                      )}
                    </p>
                  </article>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Girls Hostel Status</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">
                      Accommodation: <strong className="text-counsly-ink">{details.Hostel_Girls_Permanent_or_Rental || "Not Available"}</strong>
                    </p>
                  </article>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Hostel Room Rent & Electricity</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">
                      Room Rent: <strong className="text-counsly-ink">₹{details.Room_Rent ? Number(details.Room_Rent).toLocaleString() : 0} / year</strong><br/>
                      Electricity: <strong className="text-counsly-ink">₹{details.Electricity_Charges ? Number(details.Electricity_Charges).toLocaleString() : 0} / year</strong>
                    </p>
                  </article>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Hostel Caution Deposit</p>
                    <p className="mt-2 font-mono text-xl text-counsly-ink">
                      {details.Caution_Deposit ? `₹${Number(details.Caution_Deposit).toLocaleString()}` : "Pending"}
                    </p>
                  </article>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Hostel Establishment & Admission</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">
                      Establishment: <strong className="text-counsly-ink">₹{details.Establishment_Charges ? Number(details.Establishment_Charges).toLocaleString() : 0} / year</strong><br/>
                      Admission Fees: <strong className="text-counsly-ink">₹{details.Admission_Fees ? Number(details.Admission_Fees).toLocaleString() : 0}</strong>
                    </p>
                  </article>
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Transport Facilities</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">
                      Status: <strong className="text-counsly-ink">{details.Transport_Facilities === "no" ? "Not Available" : "✓ Available"}</strong>
                    </p>
                  </article>
                </>
              ) : (
                <>
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
                </>
              )}
            </div>
          )}

          {tab === "Placements" && (
            <div className="space-y-3">
              <h2 className="font-display text-3xl text-counsly-ink">Placement evidence</h2>
              <div className="grid gap-3 md:grid-cols-2">
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Placement rate</p>
                  <p className="mt-2 font-mono text-xl text-counsly-ink">{college.placementRate || "-"}%</p>
                </article>
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Average package</p>
                  <p className="mt-2 font-mono text-xl text-counsly-ink">{college.averagePackage || "-"} LPA</p>
                </article>
              </div>
            </div>
          )}

          {tab === "Nearby" && (
            <div className="space-y-3">
              <h2 className="font-display text-3xl text-counsly-ink">Nearby and map context</h2>
              <div className="rounded-xl border border-counsly-line bg-[radial-gradient(circle_at_20%_20%,rgba(204,120,92,0.28),transparent_36%),linear-gradient(135deg,#efe9de,#faf9f5)] p-5">
                <p className="flex gap-2 text-sm leading-6 text-counsly-body">
                  <MapPinned className="mt-1 h-4 w-4 shrink-0 text-counsly-coral" />
                  {college.latitude && college.longitude ? (
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${college.latitude},${college.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline text-counsly-coral hover:text-counsly-ink font-semibold"
                    >
                      View College Campus on Google Maps
                    </a>
                  ) : (
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(college.name)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline text-counsly-coral hover:text-counsly-ink font-semibold"
                    >
                      Search college location on Google Maps
                    </a>
                  )}
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
          <Surface className="space-y-4 p-6" tone="soft">
            <h2 className="font-display text-3xl text-counsly-ink">Nearby</h2>
            <p className="flex gap-2 text-sm leading-6 text-counsly-body">
              <TrainFront className="mt-1 h-4 w-4 shrink-0 text-counsly-coral" />
              <span>
                 {college.railway ? (
                  <a
                    href={college.railwayLatitude && college.railwayLongitude
                      ? `https://www.google.com/maps/search/?api=1&query=${college.railwayLatitude},${college.railwayLongitude}`
                      : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(college.railway + " Railway Station, Tamil Nadu")}`
                    }
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline text-counsly-coral hover:text-counsly-ink font-semibold"
                  >
                    {college.railway}
                  </a>
                ) : (
                  "Railway station context pending"
                )}
                {college.distanceKm ? `, ${college.distanceKm} km away` : " (distance pending)"}
              </span>
            </p>
            <p className="flex gap-2 text-sm leading-6 text-counsly-body">
              <MapPinned className="mt-1 h-4 w-4 shrink-0 text-counsly-teal" />
              {college.website ? (
                <a
                  href={college.website.startsWith("http") ? college.website : `https://${college.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline text-counsly-teal hover:text-counsly-ink font-semibold"
                >
                  Visit Official College Website
                </a>
              ) : (
                "Nearest TFC panel becomes district-specific after onboarding."
              )}
            </p>
          </Surface>
        </div>
      </div>
    </div>
  );
}
