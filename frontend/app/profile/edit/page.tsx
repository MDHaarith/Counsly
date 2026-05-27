"use client";

import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { fetchWorkspaceSettings, updateWorkspaceSettings } from "@/lib/api.mjs";
import { branches, districts } from "@/lib/product";

export default function ProfileEditPage() {
  const { user } = useApp();
  const [saved, setSaved] = useState(false);
  const [status, setStatus] = useState("Loading workspace defaults.");
  const [settings, setSettings] = useState({
    compactView: false,
    defaultDistrict: "Chennai",
    mobileDensity: "default",
    preferredBranches: branches.slice(0, 3).map((branch) => branch.code),
    themeMode: "mild",
  });

  const [studentContext, setStudentContext] = useState({
    chemistry: 0,
    community: "OC",
    maths: 0,
    name: "Counsly student",
    physics: 0,
    rollNumber: "",
    rollVerified: false,
    dob: "",
    generalRank: "",
    communityRank: "",
  });

  useEffect(() => {
    fetchWorkspaceSettings()
      .then((next) => {
        setSettings((current) => ({
          ...current,
          ...next,
          defaultDistrict: next.defaultDistrict || current.defaultDistrict,
          preferredBranches: next.preferredBranches.length ? next.preferredBranches : current.preferredBranches,
        }));
        setStatus("Workspace defaults loaded from the API.");
      })
      .catch(() => setStatus("API defaults unavailable. Changes remain useful in preview mode."));

    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("counsly_student_context");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setStudentContext({
            chemistry: Number(parsed.chemistry) || 0,
            community: parsed.community || "OC",
            maths: Number(parsed.maths) || 0,
            name: parsed.name || "Counsly student",
            physics: Number(parsed.physics) || 0,
            rollNumber: parsed.rollNumber || "",
            rollVerified: Boolean(parsed.rollVerified),
            dob: parsed.dob || "",
            generalRank: parsed.generalRank !== undefined && parsed.generalRank !== null ? String(parsed.generalRank) : "",
            communityRank: parsed.communityRank !== undefined && parsed.communityRank !== null ? String(parsed.communityRank) : "",
          });
        } catch (e) {
          console.error("Failed to parse student context", e);
        }
      }
    }
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const persisted = await updateWorkspaceSettings(settings);
      setSettings((current) => ({ ...current, ...persisted }));
      setStatus("Workspace defaults saved successfully.");
    } catch {
      setStatus("Defaults saved in the current form only because the workspace API did not respond.");
    }
    setSaved(true);
  };

  const toggleBranch = (code: string) => {
    setSettings((current) => ({
      ...current,
      preferredBranches: current.preferredBranches.includes(code)
        ? current.preferredBranches.filter((branch) => branch !== code)
        : [...current.preferredBranches, code],
    }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader description="Defaults for district fit, branch filters, compact density, student marks, ranks, and DOB details." eyebrow="Profile" title="Tune the workspace to the student." />
      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{status}</p>
      
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <form className="space-y-6" onSubmit={submit}>
            <Surface className="space-y-4 p-6" tone="paper">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-2xl text-counsly-ink">Workspace Settings</h2>
                <Badge>{user?.google_email ?? "Local preview profile"}</Badge>
              </div>
              <label className="field-label">
                Home district
                <select className="field" onChange={(event) => setSettings((current) => ({ ...current, defaultDistrict: event.target.value }))} value={settings.defaultDistrict}>
                  {districts.map((item) => <option key={item}>{item}</option>)}
                </select>
              </label>
              <fieldset className="space-y-2">
                <legend className="field-label">Preferred branches</legend>
                <div className="grid gap-2 md:grid-cols-2">
                  {branches.map((branch) => (
                    <label className="flex min-h-11 items-center gap-3 rounded-lg border border-counsly-line p-3 text-sm text-counsly-body" key={branch.code}>
                      <input checked={settings.preferredBranches.includes(branch.code)} onChange={() => toggleBranch(branch.code)} type="checkbox" />
                      {branch.name}
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="grid gap-2 md:grid-cols-2">
                <label className="flex min-h-11 items-center gap-3 rounded-lg border border-counsly-line p-3 text-sm text-counsly-body">
                  <input checked={settings.compactView} onChange={(event) => setSettings((current) => ({ ...current, compactView: event.target.checked }))} type="checkbox" />
                  Use compact choice density
                </label>
                <label className="field-label">
                  Mobile density
                  <select className="field" onChange={(event) => setSettings((current) => ({ ...current, mobileDensity: event.target.value }))} value={settings.mobileDensity}>
                    <option value="default">Default</option>
                    <option value="compact">Compact</option>
                    <option value="comfortable">Comfortable</option>
                  </select>
                </label>
              </div>
              <button className="button-primary w-fit" type="submit">Save workspace defaults</button>
            </Surface>
          </form>

          <Surface className="space-y-4 p-6" tone="paper">
            <h2 className="font-display text-2xl text-counsly-ink">Student Profile Details</h2>
            <p className="text-xs text-counsly-body">Capture core ranks, DOB, and scores used in eligibility and cutoff calculations.</p>
            
            <div className="grid gap-4 md:grid-cols-2">
              <label className="field-label">
                Student name
                <input
                  type="text"
                  className="field"
                  value={studentContext.name}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, name: e.target.value }))}
                  required
                />
              </label>
              <label className="field-label">
                Date of birth
                <input
                  type="date"
                  className="field"
                  value={studentContext.dob}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, dob: e.target.value }))}
                  required
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <label className="field-label">
                Mathematics (Max 100)
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="field font-mono"
                  value={studentContext.maths}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, maths: Number(e.target.value) }))}
                  required
                />
              </label>
              <label className="field-label">
                Physics (Max 50)
                <input
                  type="number"
                  min="0"
                  max="50"
                  className="field font-mono"
                  value={studentContext.physics}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, physics: Number(e.target.value) }))}
                  required
                />
              </label>
              <label className="field-label">
                Chemistry (Max 50)
                <input
                  type="number"
                  min="0"
                  max="50"
                  className="field font-mono"
                  value={studentContext.chemistry}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, chemistry: Number(e.target.value) }))}
                  required
                />
              </label>
            </div>

            <div className="bg-counsly-soft rounded-lg p-3 border border-counsly-line flex items-center justify-between">
              <span className="text-xs font-bold text-counsly-body">Computed Cutoff:</span>
              <span className="text-base font-extrabold text-counsly-coral font-mono">
                {(Number(studentContext.maths) + Number(studentContext.physics) + Number(studentContext.chemistry)).toFixed(2)} / 200
              </span>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="field-label">
                Community / Category
                <select
                  className="field"
                  value={studentContext.community}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, community: e.target.value }))}
                >
                  {["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
              <label className="field-label">
                Roll number
                <input
                  type="text"
                  className="field font-mono"
                  value={studentContext.rollNumber}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, rollNumber: e.target.value }))}
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="field-label">
                TNEA Overall General Rank (Optional)
                <input
                  type="number"
                  className="field font-mono"
                  placeholder="e.g. 1524"
                  value={studentContext.generalRank}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, generalRank: e.target.value }))}
                />
              </label>
              <label className="field-label">
                TNEA Community Rank (Optional)
                <input
                  type="number"
                  className="field font-mono"
                  placeholder="e.g. 341"
                  value={studentContext.communityRank}
                  onChange={(e) => setStudentContext((prev) => ({ ...prev, communityRank: e.target.value }))}
                />
              </label>
            </div>
            
            <button
              className="button-primary w-fit animate-fade-in"
              type="button"
              onClick={() => {
                if (typeof window !== "undefined") {
                  localStorage.setItem(
                    "counsly_student_context",
                    JSON.stringify({
                      ...studentContext,
                      maths: Number(studentContext.maths),
                      physics: Number(studentContext.physics),
                      chemistry: Number(studentContext.chemistry),
                      generalRank: studentContext.generalRank === "" ? null : Number(studentContext.generalRank),
                      communityRank: studentContext.communityRank === "" ? null : Number(studentContext.communityRank),
                    })
                  );
                  setStatus("Student profile details successfully saved to local workspace store.");
                  setSaved(true);
                }
              }}
            >
              Save Student Details
            </button>
          </Surface>
        </div>

        <Surface className="space-y-4 p-6 h-fit" tone="soft">
          <h2 className="font-display text-3xl text-counsly-ink">Workspace boundary</h2>
          <p className="text-sm leading-6 text-counsly-body">Choices, compares, snapshots, and settings stay private to this student profile.</p>
          {saved && (
            <p className="flex items-center gap-2 rounded-lg bg-counsly-safe/15 p-3 text-sm text-counsly-ink animate-slide-up">
              <CheckCircle2 className="h-4 w-4 text-counsly-safe" />
              Profile changes saved successfully.
            </p>
          )}
        </Surface>
      </div>
    </div>
  );
}
