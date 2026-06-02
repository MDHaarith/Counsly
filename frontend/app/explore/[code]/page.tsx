"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Bus, GitCompareArrows, MapPinned, TrainFront, User, Sliders } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { FeatureGate } from "@/components/feature-gate";
import { choiceWriteDestination } from "@/lib/access.mjs";
import { addChoice, fetchCollegeDetail } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { currency, getCollege, trendRows, cleanCollegeName } from "@/lib/product";

const tabs = ["Overview", "Cutoffs", "Fees & Facilities", "Placements", "Nearby"] as const;

function CollegeInsightContent({ params }: { params: { code: string } }) {
  const preview = useMemo(() => getCollege(params.code), [params.code]);
  const { user } = useApp();
  const router = useRouter();
  const [college, setCollege] = useState<any>(preview);
  const [tab, setTab] = useState<(typeof tabs)[number]>("Overview");
  const [status, setStatus] = useState("Loading live college detail and community-safe branch data.");
  const [choiceStatus, setChoiceStatus] = useState("");
  const [studentCommunity, setStudentCommunity] = useState<string>("OC");
  const [studentContext, setStudentContext] = useState<any>(null);

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
    
    // Resolve community category from client context
    let community = "OC";
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("counsly_student_context");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setStudentContext(parsed);
          if (parsed.community) {
            community = parsed.community;
            setStudentCommunity(parsed.community);
          }
        } catch (e) {}
      }
    }

    fetchCollegeDetail(params.code, community)
      .then((detail) => {
        if (!active) return;
        setCollege(detail);
        setStatus(`Live college detail loaded from the workspace API for category ${community}.`);
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

  useEffect(() => {
    if (typeof window !== "undefined") {
      const qParams = new URLSearchParams(window.location.search);
      const tabParam = qParams.get("tab");
      if (tabParam && tabs.includes(tabParam as any)) {
        setTab(tabParam as any);
      }
    }
  }, []);

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
                      {(() => {
                        const rawAcct = details.Bank_A_c_No?.toString().trim();
                        const isAcctEmptyOrZero = !rawAcct || rawAcct === "" || /^[0\s\-]*$/.test(rawAcct);
                        return (
                          <>
                            {details.Bank_Name && details.Bank_Name !== "-" && details.Bank_Name.trim() !== "" && (
                              <p>Bank Name: <strong className="text-counsly-ink">{details.Bank_Name}</strong></p>
                            )}
                            {!isAcctEmptyOrZero && (
                              <p>Account Number: <strong className="text-counsly-ink font-mono">{rawAcct}</strong></p>
                            )}
                          </>
                        );
                      })()}
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
            <div className="space-y-4">
              <div className="border-b border-counsly-line pb-2">
                <p className="eyebrow">Active branch cutoff insight</p>
                <h3 className="font-display text-2xl text-counsly-ink mt-1">
                  {college.branchCode} - {college.branchName}
                </h3>
              </div>

              {/* Core Branch Metrics */}
              <div className="grid gap-3 sm:grid-cols-3 text-sm">
                <div className="rounded-lg border border-counsly-line bg-counsly-soft p-4">
                  <p className="eyebrow text-counsly-muted">{studentCommunity} Quota Seats</p>
                  <strong className="block font-mono text-lg text-counsly-ink mt-1">
                    {(() => {
                      const activeBranch = branches.find((b: any) => b.code === college.branchCode);
                      const seatPayload = activeBranch?.seats;
                      const totalSeats = seatPayload?.total || activeBranch?.approved_intake || college.seats || 0;
                      if (seatPayload?.available !== undefined) {
                        return `${seatPayload.available} / ${totalSeats}`;
                      }
                      const commKey = studentCommunity.toLowerCase();
                      const legacySeats = seatPayload?.[commKey];
                      return legacySeats !== undefined ? `${legacySeats} / ${totalSeats}` : totalSeats;
                    })()}
                  </strong>
                </div>
                <div className="rounded-lg border border-counsly-line bg-counsly-soft p-4">
                  <p className="eyebrow text-counsly-muted">Last cutoff rank</p>
                  <strong className="block font-mono text-lg text-counsly-ink mt-1">{college.cutoffRank || "Pending"}</strong>
                </div>
                <div className="rounded-lg border border-counsly-line bg-counsly-soft p-4">
                  <p className="eyebrow text-counsly-muted">Cutoff trend</p>
                  <strong className="block text-lg text-counsly-ink mt-1">
                    {cutoffRows.length > 1 && cutoffRows[0].cutoff_mark > cutoffRows[cutoffRows.length - 1].cutoff_mark ? "Rising" : "Stable"}
                  </strong>
                </div>
              </div>

              {/* Historical Cutoff Trend List */}
              <div className="space-y-2 pt-2">
                <h4 className="font-display font-medium text-lg text-counsly-ink">Historical Cutoff Movement</h4>
                <div className="space-y-2">
                  {(cutoffRows.length ? cutoffRows : trendRows.slice(1)).map((row: { year: number | string; cutoff_mark?: number; ambitious?: number }) => (
                    <div className="grid grid-cols-[70px_1fr_auto] items-center gap-3 rounded-lg bg-counsly-soft/50 px-4 py-3" key={row.year}>
                      <span className="font-mono text-sm font-semibold text-counsly-muted">{row.year}</span>
                      <span className="text-sm text-counsly-body">Cutoff Mark</span>
                      <strong className="font-mono text-base text-counsly-ink">{row.cutoff_mark ?? row.ambitious}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {tab === "Fees & Facilities" && (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <article className="rounded-lg border border-counsly-line p-4">
                  <p className="eyebrow">Annual tuition fees</p>
                  <p className="mt-2 font-mono text-xl text-counsly-ink">{college.fees ? currency(college.fees) : "Pending"}</p>
                </article>
                
                {details ? (
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Transport Facilities</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">
                      Status: <strong className="text-counsly-ink">{details.Transport_Facilities === "no" ? "Not Available" : "✓ Available"}</strong>
                    </p>
                  </article>
                ) : (
                  <article className="rounded-lg border border-counsly-line p-4">
                    <p className="eyebrow">Transport</p>
                    <p className="mt-2 text-sm leading-6 text-counsly-body">{college.transport ? "✓ Available" : "Not listed"} in the current data surface.</p>
                  </article>
                )}
              </div>

              {details ? (
                <article className="rounded-lg border border-counsly-line p-5 bg-counsly-soft/50 space-y-4">
                  <div className="flex items-center gap-2 border-b border-counsly-line pb-2">
                    <span className="p-1.5 rounded-lg bg-counsly-coral/10 text-counsly-coral">
                      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 20v-8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v8"/><path d="M5 10V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><circle cx="12" cy="14" r="2"/></svg>
                    </span>
                    <p className="font-display font-semibold text-lg text-counsly-ink">Hostel Facilities & Fees</p>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-counsly-muted">Accommodation</h4>
                      <div className="text-sm space-y-1.5 text-counsly-body">
                        <p>Boys Hostel: <strong className="text-counsly-ink">{details.Hostel_Boys_Permanent_or_Rental || "Not Available"}</strong></p>
                        <p>Girls Hostel: <strong className="text-counsly-ink">{details.Hostel_Girls_Permanent_or_Rental || "Not Available"}</strong></p>
                        {details.Type_of_Mess && details.Type_of_Mess !== "-" && (
                          <p>Mess Type: <strong className="text-counsly-ink">{details.Type_of_Mess}</strong></p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-counsly-muted">Charges & Deposits</h4>
                      <div className="text-sm space-y-1.5 text-counsly-body">
                        <p>Caution Deposit: <strong className="text-counsly-ink">{details.Caution_Deposit ? `₹${Number(details.Caution_Deposit).toLocaleString()}` : "Pending"}</strong></p>
                        <p>Room Rent: <strong className="text-counsly-ink">₹{details.Room_Rent ? Number(details.Room_Rent).toLocaleString() : 0} / year</strong></p>
                        <p>Electricity: <strong className="text-counsly-ink">₹{details.Electricity_Charges ? Number(details.Electricity_Charges).toLocaleString() : 0} / year</strong></p>
                        <p>Establishment: <strong className="text-counsly-ink">₹{details.Establishment_Charges ? Number(details.Establishment_Charges).toLocaleString() : 0} / year</strong></p>
                        <p>Admission Fee: <strong className="text-counsly-ink">₹{details.Admission_Fees ? Number(details.Admission_Fees).toLocaleString() : 0}</strong></p>
                      </div>
                    </div>
                  </div>
                </article>
              ) : (
                <article className="rounded-lg border border-counsly-line p-5 bg-counsly-soft/50 space-y-3">
                  <p className="font-display font-semibold text-lg text-counsly-ink">Hostel Details</p>
                  <p className="text-sm leading-6 text-counsly-body">
                    Status: <strong className="text-counsly-ink">{college.hostel ? "✓ Available" : "Not listed"}</strong>
                  </p>
                  <p className="text-xs text-counsly-muted">Monthly room cost, mess food type, and hostel caution deposit details will show here when verified source rows are audited.</p>
                </article>
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
            
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-counsly-muted uppercase font-bold tracking-wider mb-1">Local Station</p>
                <p className="flex gap-2 text-sm leading-6 text-counsly-body">
                  <TrainFront className="mt-1 h-4 w-4 shrink-0 text-[#1d4ed8]" />
                  <span>
                     {college.railway ? (
                      <a
                        href={college.railwayLatitude && college.railwayLongitude
                          ? `https://www.google.com/maps/search/?api=1&query=${college.railwayLatitude},${college.railwayLongitude}`
                          : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(college.railway + " Railway Station, Tamil Nadu")}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-[#1d4ed8] hover:text-counsly-ink font-semibold"
                      >
                        {college.railway}
                      </a>
                    ) : (
                      "Railway station context pending"
                    )}
                    {college.distanceKm ? `, ${college.distanceKm.toFixed(0)} km away` : " (distance pending)"}
                  </span>
                </p>
              </div>

              {college.expressStation && (
                <div>
                  <p className="text-[10px] text-counsly-muted uppercase font-bold tracking-wider mb-1">Express Transit Hub</p>
                  <p className="flex gap-2 text-sm leading-6 text-counsly-body">
                    <TrainFront className="mt-1 h-4 w-4 shrink-0 text-[#7c3aed]" />
                    <span>
                      <a
                        href={college.expressStationLatitude && college.expressStationLongitude
                          ? `https://www.google.com/maps/search/?api=1&query=${college.expressStationLatitude},${college.expressStationLongitude}`
                          : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(college.expressStation + " Railway Station, Tamil Nadu")}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-[#7c3aed] hover:text-counsly-ink font-semibold"
                      >
                        {college.expressStation}
                      </a>
                      {college.expressStationDistanceKm ? `, ${college.expressStationDistanceKm.toFixed(0)} km away` : " (distance pending)"}
                    </span>
                  </p>
                </div>
              )}

              {college.busStation && (
                <div>
                  <p className="text-[10px] text-counsly-muted uppercase font-bold tracking-wider mb-1">Nearest Regional Bus Terminus</p>
                  <p className="flex gap-2 text-sm leading-6 text-counsly-body">
                    <Bus className="mt-1 h-4 w-4 shrink-0 text-[#15803d]" />
                    <span>
                      <a
                        href={college.busStationLatitude && college.busStationLongitude
                          ? `https://www.google.com/maps/search/?api=1&query=${college.busStationLatitude},${college.busStationLongitude}`
                          : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(college.busStation + " Bus Stand, Tamil Nadu")}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-[#15803d] hover:text-counsly-ink font-semibold"
                      >
                        {college.busStation}
                      </a>
                      {college.busStationDistanceKm ? `, ${college.busStationDistanceKm.toFixed(0)} km away` : " (distance pending)"}
                    </span>
                  </p>
                </div>
              )}

              {college.busStop && (
                <div>
                  <p className="text-[10px] text-counsly-muted uppercase font-bold tracking-wider mb-1">Nearest Local Bus Stop</p>
                  <p className="flex gap-2 text-sm leading-6 text-counsly-body">
                    <Bus className="mt-1 h-4 w-4 shrink-0 text-emerald-600" />
                    <span>
                      <a
                        href={college.busStopLatitude && college.busStopLongitude
                          ? `https://www.google.com/maps/search/?api=1&query=${college.busStopLatitude},${college.busStopLongitude}`
                          : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(college.busStop + " Bus Stop, Tamil Nadu")}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline text-emerald-600 hover:text-counsly-ink font-semibold"
                      >
                        {college.busStop}
                      </a>
                      {college.busStopDistanceKm ? `, ${college.busStopDistanceKm.toFixed(0)} km away` : " (distance pending)"}
                    </span>
                  </p>
                </div>
              )}
            </div>

            <p className="flex gap-2 text-sm leading-6 text-counsly-body border-t border-counsly-line pt-3">
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
                "Official website is not available."
              )}
            </p>
          </Surface>

          {/* Student Profile & Counseling Calculator */}
          <Surface className="space-y-4 p-6" tone="soft">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-xl font-bold text-counsly-ink flex items-center gap-2">
                <User className="h-5 w-5 text-counsly-coral" />
                <span>Student Profile</span>
              </h2>
              <Badge tone="coral">TNEA 2027</Badge>
            </div>
            
            {studentContext ? (
              <div className="space-y-3 pt-2 text-sm text-counsly-body">
                <div className="flex justify-between border-b border-counsly-line pb-2">
                  <span className="text-counsly-muted">Student Name</span>
                  <span className="font-semibold text-counsly-ink truncate max-w-[150px]">{studentContext.name || "Counsly Student"}</span>
                </div>
                <div className="flex justify-between border-b border-counsly-line pb-2">
                  <span className="text-counsly-muted">Cutoff Aggregate</span>
                  <span className="font-mono font-bold text-counsly-coral bg-white px-2 py-0.5 rounded border border-counsly-line">
                    {(Number(studentContext.maths || 0) + Number(studentContext.physics || 0) + Number(studentContext.chemistry || 0)).toFixed(2)} / 200
                  </span>
                </div>
                <div className="flex justify-between border-b border-counsly-line pb-2">
                  <span className="text-counsly-muted">Community Quota</span>
                  <span className="font-semibold text-counsly-ink">{studentContext.community || "OC"}</span>
                </div>
                <div className="flex justify-between border-b border-counsly-line pb-2">
                  <span className="text-counsly-muted">Verification Status</span>
                  <span className={`font-semibold ${studentContext.rollVerified ? "text-emerald-600" : "text-amber-600"}`}>
                    {studentContext.rollVerified ? "Verified Roll Number" : "Unverified Profile"}
                  </span>
                </div>
                <div className="pt-2">
                  <Link href="/profile/edit" className="button-primary w-full text-center flex items-center justify-center gap-1.5 py-2">
                    <Sliders className="h-4 w-4" />
                    Edit Profile & Marks
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-3 pt-2 text-sm text-counsly-body">
                <p className="text-counsly-muted leading-relaxed">
                  Set up your marks and community quota to view personalized eligible cutoffs for this college.
                </p>
                <div className="pt-2">
                  <Link href="/profile/edit" className="button-primary w-full text-center flex items-center justify-center gap-1.5 py-2">
                    <Sliders className="h-4 w-4" />
                    Create Student Profile
                  </Link>
                </div>
              </div>
            )}
          </Surface>
        </div>
      </div>
    </div>
  );
}

export default function CollegeInsightPage(props: { params: { code: string } }) {
  return (
    <FeatureGate>
      <CollegeInsightContent {...props} />
    </FeatureGate>
  );
}
