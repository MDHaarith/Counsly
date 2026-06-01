
"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Award,
  Check,
  CheckCircle2,
  Compass,
  RefreshCw,
  User,
} from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface, StatusToast } from "@/components/ui";
import { fetchWorkspaceSettings, updateWorkspaceSettings, verifyRollNumber } from "@/lib/api.mjs";
import { branches, districts } from "@/lib/product";

const COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"];

const COMMUNITY_NOTES: Record<string, string> = {
  OC: "Open Competition",
  BC: "Backward Class",
  BCM: "Backward Class Muslim",
  MBC: "Most Backward Class / Denotified Communities",
  SC: "Scheduled Caste",
  SCA: "Scheduled Caste Arunthathiyar",
  ST: "Scheduled Tribe",
};

function clampNumber(value: string, max: number) {
  if (value === "") return 0;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 0;
  return Math.min(max, Math.max(0, parsed));
}

export default function ProfileEditPage() {
  const { user } = useApp();
  const [saved, setSaved] = useState(false);
  const [toast, setToast] = useState<{ message: string; tone: "success" | "error" | "default" } | null>(null);
  const [hasUnsavedProfile, setHasUnsavedProfile] = useState(false);

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

  const computedCutoff = useMemo(() => {
    return Number(studentContext.maths) + Number(studentContext.physics) + Number(studentContext.chemistry);
  }, [studentContext.chemistry, studentContext.maths, studentContext.physics]);

  const isEligible = computedCutoff >= 78;

  const showToast = (message: string, tone: "success" | "error" | "default" = "default") => {
    setToast({ message, tone });
  };

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    fetchWorkspaceSettings()
      .then((next) => {
        setSettings((current) => ({
          ...current,
          ...next,
          defaultDistrict: next.defaultDistrict || current.defaultDistrict,
          preferredBranches: next.preferredBranches.length ? next.preferredBranches : current.preferredBranches,
        }));
      })
      .catch(() => showToast("Using local settings until sync is available.", "default"));

    if (typeof window === "undefined") return;
    const stored = localStorage.getItem("counsly_student_context");
    if (!stored) return;
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
    } catch (error) {
      console.error("Failed to parse student context", error);
    }
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const persisted = await updateWorkspaceSettings(settings);
      setSettings((current) => ({ ...current, ...persisted }));
      showToast("Workspace settings saved.", "success");
    } catch {
      showToast("Workspace settings saved locally.", "default");
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

  const updateStudentField = (field: keyof typeof studentContext, value: string | number | boolean) => {
    setStudentContext((current) => ({ ...current, [field]: value }));
    setHasUnsavedProfile(true);
  };

  const handleSaveStudentDetails = () => {
    if (typeof window === "undefined") return;
    localStorage.setItem(
      "counsly_student_context",
      JSON.stringify({
        ...studentContext,
        maths: Number(studentContext.maths),
        physics: Number(studentContext.physics),
        chemistry: Number(studentContext.chemistry),
        generalRank: studentContext.generalRank === "" ? null : Number(studentContext.generalRank),
        communityRank: studentContext.communityRank === "" ? null : Number(studentContext.communityRank),
      }),
    );
    showToast("Student profile saved.", "success");
    setSaved(true);
    setHasUnsavedProfile(false);
  };

  const handleRollNumberVerification = async () => {
    const roll = studentContext.rollNumber.trim();
    if (!roll) {
      showToast("Enter a TNEA roll number before verification.", "default");
      return;
    }
    try {
      const response = await verifyRollNumber(roll);
      if (response?.success) {
        setStudentContext((current) => ({
          ...current,
          rollVerified: true,
          community: response.community || current.community,
          generalRank: response.official_rank !== undefined ? String(response.official_rank) : current.generalRank,
        }));
        showToast(`Roll number verified. Rank: ${response.official_rank}`, "success");
        setHasUnsavedProfile(true);
      }
    } catch (error: any) {
      showToast(error.message || "Roll number verification failed.", "error");
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {toast && (
        <div className="fixed bottom-24 right-6 z-50 animate-slide-up">
          <StatusToast message={toast.message} tone={toast.tone} />
        </div>
      )}

      <PageHeader
        description="Keep the details used for counseling recommendations accurate: marks, ranks, community, district, and preferred branches."
        eyebrow="Profile"
        title="Student Details"
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <Surface className="p-6" tone="paper">
            <div className="flex flex-col gap-2 border-b border-counsly-line pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="flex items-center gap-2 font-display text-2xl text-counsly-ink">
                  <User className="h-5 w-5 text-counsly-coral" />
                  Academic details
                </h2>
                <p className="mt-1 text-sm text-counsly-muted">These values are stored locally in this browser.</p>
              </div>
              <Badge tone={hasUnsavedProfile ? "warning" : "neutral"}>
                {hasUnsavedProfile ? "Unsaved changes" : "No pending edits"}
              </Badge>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <label className="field-label">
                Student full name
                <input
                  className="field mt-1.5 bg-white"
                  onChange={(event) => updateStudentField("name", event.target.value)}
                  placeholder="Name as used for counseling"
                  type="text"
                  value={studentContext.name}
                />
              </label>
              <label className="field-label">
                Date of birth
                <input
                  className="field mt-1.5 bg-white"
                  onChange={(event) => updateStudentField("dob", event.target.value)}
                  type="date"
                  value={studentContext.dob}
                />
              </label>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <label className="field-label">
                Mathematics mark / 100
                <input
                  className="field mt-1.5 bg-white font-mono"
                  max="100"
                  min="0"
                  onChange={(event) => updateStudentField("maths", clampNumber(event.target.value, 100))}
                  step="0.5"
                  type="number"
                  value={studentContext.maths}
                />
              </label>
              <label className="field-label">
                Physics mark / 50
                <input
                  className="field mt-1.5 bg-white font-mono"
                  max="50"
                  min="0"
                  onChange={(event) => updateStudentField("physics", clampNumber(event.target.value, 50))}
                  step="0.25"
                  type="number"
                  value={studentContext.physics}
                />
              </label>
              <label className="field-label">
                Chemistry mark / 50
                <input
                  className="field mt-1.5 bg-white font-mono"
                  max="50"
                  min="0"
                  onChange={(event) => updateStudentField("chemistry", clampNumber(event.target.value, 50))}
                  step="0.25"
                  type="number"
                  value={studentContext.chemistry}
                />
              </label>
            </div>

            <div className="mt-6 rounded-lg border border-counsly-line bg-counsly-soft px-4 py-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.14em] text-counsly-muted">Current cutoff</p>
                  <p className="mt-1 font-mono text-2xl font-semibold text-counsly-ink">{computedCutoff.toFixed(2)} / 200</p>
                </div>
                <Badge tone={isEligible ? "safe" : "warning"}>
                  {isEligible ? "Eligible threshold met" : "Below 78.00 threshold"}
                </Badge>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
              <label className="field-label">
                TNEA roll number
                <div className="mt-1.5 flex gap-2">
                  <input
                    className="field bg-white font-mono"
                    onChange={(event) => {
                      setStudentContext((current) => ({ ...current, rollNumber: event.target.value, rollVerified: false }));
                      setHasUnsavedProfile(true);
                    }}
                    placeholder="Enter roll number"
                    type="text"
                    value={studentContext.rollNumber}
                  />
                  <button
                    className="button-secondary shrink-0 px-3"
                    onClick={handleRollNumberVerification}
                    type="button"
                  >
                    {studentContext.rollVerified ? <CheckCircle2 className="h-4 w-4 text-counsly-teal" /> : <RefreshCw className="h-4 w-4" />}
                    {studentContext.rollVerified ? "Verified" : "Verify"}
                  </button>
                </div>
              </label>

              <label className="field-label">
                Community
                <select
                  className="field mt-1.5 bg-white"
                  onChange={(event) => updateStudentField("community", event.target.value)}
                  value={studentContext.community}
                >
                  {COMMUNITIES.map((community) => (
                    <option key={community} value={community}>
                      {community}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <label className="field-label">
                General rank
                <input
                  className="field mt-1.5 bg-white font-mono"
                  min="1"
                  onChange={(event) => updateStudentField("generalRank", event.target.value)}
                  placeholder="Optional"
                  type="number"
                  value={studentContext.generalRank}
                />
              </label>
              <label className="field-label">
                Community rank
                <input
                  className="field mt-1.5 bg-white font-mono"
                  min="1"
                  onChange={(event) => updateStudentField("communityRank", event.target.value)}
                  placeholder="Optional"
                  type="number"
                  value={studentContext.communityRank}
                />
              </label>
            </div>

            <div className="mt-6 flex flex-col gap-3 border-t border-counsly-line pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="flex items-center gap-2 text-sm text-counsly-muted">
                {hasUnsavedProfile ? <AlertCircle className="h-4 w-4 text-counsly-coral" /> : <Check className="h-4 w-4 text-counsly-teal" />}
                {hasUnsavedProfile ? "Save academic details before using recommendations." : "Academic details are saved locally."}
              </p>
              <button className="button-primary" onClick={handleSaveStudentDetails} type="button">
                Save academic details
              </button>
            </div>
          </Surface>

          <form onSubmit={submit}>
            <Surface className="p-6" tone="paper">
              <div className="border-b border-counsly-line pb-4">
                <h2 className="flex items-center gap-2 font-display text-2xl text-counsly-ink">
                  <Compass className="h-5 w-5 text-counsly-coral" />
                  Workspace settings
                </h2>
                <p className="mt-1 text-sm text-counsly-muted">{user?.google_email ?? "Local student workspace"}</p>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="field-label">
                  Home district
                  <select
                    className="field mt-1.5 bg-white"
                    onChange={(event) => setSettings((current) => ({ ...current, defaultDistrict: event.target.value }))}
                    value={settings.defaultDistrict}
                  >
                    {districts.map((district) => (
                      <option key={district}>{district}</option>
                    ))}
                  </select>
                </label>

                <label className="field-label">
                  Mobile display density
                  <select
                    className="field mt-1.5 bg-white"
                    onChange={(event) => setSettings((current) => ({ ...current, mobileDensity: event.target.value }))}
                    value={settings.mobileDensity}
                  >
                    <option value="default">Default</option>
                    <option value="compact">Compact</option>
                    <option value="comfortable">Comfortable</option>
                  </select>
                </label>
              </div>

              <fieldset className="mt-6">
                <legend className="field-label">Preferred branches</legend>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {branches.map((branch) => {
                    const selected = settings.preferredBranches.includes(branch.code);
                    return (
                      <label
                        className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm ${
                          selected ? "border-counsly-coral bg-counsly-soft text-counsly-ink" : "border-counsly-line bg-white text-counsly-body"
                        }`}
                        key={branch.code}
                      >
                        <input
                          checked={selected}
                          className="h-4 w-4 accent-counsly-coral"
                          onChange={() => toggleBranch(branch.code)}
                          type="checkbox"
                        />
                        <span className="font-mono text-xs font-semibold">{branch.code}</span>
                        <span className="truncate">{branch.name}</span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <div className="mt-6 flex flex-col gap-3 border-t border-counsly-line pt-4 sm:flex-row sm:items-center sm:justify-between">
                <label className="flex items-center gap-3 text-sm font-medium text-counsly-body">
                  <input
                    checked={settings.compactView}
                    className="h-4 w-4 accent-counsly-coral"
                    onChange={(event) => setSettings((current) => ({ ...current, compactView: event.target.checked }))}
                    type="checkbox"
                  />
                  Use compact desktop rows
                </label>
                <button className="button-primary" type="submit">
                  Save workspace settings
                </button>
              </div>
            </Surface>
          </form>
        </div>

        <aside className="space-y-4">
          <Surface className="p-5" tone="paper">
            <div className="flex items-center justify-between border-b border-counsly-line pb-3">
              <h2 className="font-display text-xl text-counsly-ink">Summary</h2>
              <Award className="h-5 w-5 text-counsly-coral" />
            </div>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-counsly-muted">Cutoff</dt>
                <dd className="font-mono font-semibold text-counsly-ink">{computedCutoff.toFixed(2)}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-counsly-muted">Eligibility</dt>
                <dd className={isEligible ? "font-medium text-counsly-ink" : "font-medium text-counsly-coral"}>
                  {isEligible ? "Meets threshold" : "Below threshold"}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-counsly-muted">Community</dt>
                <dd className="font-medium text-counsly-ink">{studentContext.community}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-counsly-muted">Roll number</dt>
                <dd className="font-medium text-counsly-ink">{studentContext.rollVerified ? "Verified" : "Not verified"}</dd>
              </div>
            </dl>
          </Surface>

          <Surface className="p-5" tone="paper">
            <h2 className="font-display text-xl text-counsly-ink">Community group</h2>
            <p className="mt-2 text-sm leading-6 text-counsly-body">
              {COMMUNITY_NOTES[studentContext.community] || "Select a community group."}
            </p>
          </Surface>

          <Surface className="p-5" tone="paper">
            <h2 className="font-display text-xl text-counsly-ink">Data storage</h2>
            <p className="mt-2 text-sm leading-6 text-counsly-body">
              Student marks, ranks, date of birth, and roll number are stored in browser local storage. Workspace settings sync through the backend when available.
            </p>
            {saved && (
              <p className="mt-4 flex items-center gap-2 rounded-lg border border-counsly-line bg-counsly-soft p-3 text-sm font-medium text-counsly-ink">
                <Check className="h-4 w-4 text-counsly-teal" />
                Recent changes saved.
              </p>
            )}
          </Surface>
        </aside>
      </div>
    </div>
  );
}
