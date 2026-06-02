"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "../AppContext";
import { AlertTriangle, ChevronRight, Shield, UserCheck } from "lucide-react";
import confetti from "canvas-confetti";

import { runOnboarding, verifyRollNumber } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";
import { submitStep1Eligibility } from "@/lib/onboarding-flow.mjs";
import { Surface, Badge } from "@/components/ui";

export function OnboardingWizard({ initialStep = 1 }: { initialStep?: number }) {
  const router = useRouter();
  const { user, setWorkspaceOnboardingStep } = useApp();

  const normalizedInitialStep = initialStep > 2 ? 2 : initialStep;
  const [step, setStep] = useState(normalizedInitialStep);
  const [maths, setMaths] = useState<number | "">("");
  const [physics, setPhysics] = useState<number | "">("");
  const [chemistry, setChemistry] = useState<number | "">("");
  const [community, setCommunity] = useState("OC");
  const [rollNumber, setRollNumber] = useState("");
  const [rollVerified, setRollVerified] = useState(false);
  const [dob, setDob] = useState("");
  const [generalRank, setGeneralRank] = useState<number | "">("");
  const [communityRank, setCommunityRank] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [denied, setDenied] = useState(false);
  const [backendOnboardingConfirmed, setBackendOnboardingConfirmed] = useState(false);
  const trackedStart = useRef(false);

  useEffect(() => {
    if (!user) {
      router.push("/");
    } else if (user.workspace_onboarding_step === "completed") {
      router.push("/dashboard");
    }
  }, [user, router]);

  useEffect(() => {
    if (!user || trackedStart.current) return;
    trackedStart.current = true;
    trackFunnelEvent("onboarding_started", { step: normalizedInitialStep, user });
  }, [normalizedInitialStep, user]);

  const handleVerifyRoll = async () => {
    if (!rollNumber.trim()) {
      setErrorMsg("Please enter a valid TNEA Roll Number.");
      return;
    }
    setErrorMsg("");
    try {
      const res = await verifyRollNumber(rollNumber);
      if (res && res.success) {
        setRollVerified(true);
        setCommunity(res.community || community);
        if (res.official_rank) {
          setGeneralRank(res.official_rank);
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to verify roll number.");
    }
  };

  const getAggregate = () => {
    const m = Number(maths) || 0;
    const p = Number(physics) || 0;
    const c = Number(chemistry) || 0;
    return m + p + c;
  };

  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");

    const m = Number(maths);
    const p = Number(physics);
    const c = Number(chemistry);

    if (m > 100 || p > 50 || c > 50 || m < 0 || p < 0 || c < 0) {
      setErrorMsg("Maths must be within 0-100. Physics and Chemistry must be within 0-50.");
      return;
    }

    const agg = getAggregate();
    if (agg < 78) {
      setDenied(true);
      return;
    }

    setLoading(true);
    setBackendOnboardingConfirmed(false);
    try {
      const result = await submitStep1Eligibility({
        maths: m,
        physics: p,
        chemistry: c,
        runOnboarding,
      });

      if (result.backendConfirmed && result.nextStep === 2) {
        setBackendOnboardingConfirmed(true);
        setStep(2);
      } else {
        setErrorMsg(result.errorMsg);
        setStep(1);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteOnboarding = () => {
    setLoading(true);
    setTimeout(() => {
      if (!backendOnboardingConfirmed) {
        setErrorMsg("Backend onboarding confirmation is required before completing setup. Please verify eligibility again.");
        setStep(1);
        setLoading(false);
        return;
      }

      localStorage.setItem(
        "counsly_student_context",
        JSON.stringify({
          chemistry: Number(chemistry),
          community,
          maths: Number(maths),
          name: user?.name || "Counsly student",
          physics: Number(physics),
          rollNumber: rollNumber.trim(),
          rollVerified,
          dob,
          generalRank: generalRank === "" ? null : Number(generalRank),
          communityRank: communityRank === "" ? null : Number(communityRank),
        }),
      );
      trackFunnelEvent("onboarding_completed", {
        aggregate: getAggregate(),
        community,
        roll_verified: rollVerified,
        user,
      });
      setWorkspaceOnboardingStep("completed");
      confetti({
        particleCount: 150,
        spread: 80,
        origin: { y: 0.6 },
      });
      router.push("/dashboard");
      setLoading(false);
    }, 1000);
  };

  const handleStep2Submit = (e: React.FormEvent) => {
    e.preventDefault();
    handleCompleteOnboarding();
  };

  if (denied) {
    return (
      <div className="max-w-md mx-auto my-12 animate-slide-up">
        <Surface className="p-8 text-center space-y-6" tone="paper">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-500 mx-auto animate-pulse">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <h2 className="font-display text-3xl text-counsly-ink tracking-tight">Cutoff Eligibility Denied</h2>
          <p className="text-sm leading-relaxed text-counsly-muted">
            Under current TNEA guidelines, an aggregate score below <span className="text-red-500 font-semibold">78.0 / 200</span> does not meet the eligibility gate threshold.
          </p>
          <div className="bg-counsly-soft rounded-lg p-4 border border-counsly-line text-left space-y-3">
            <span className="block text-xs font-semibold uppercase tracking-wider text-counsly-muted">Your Metrics:</span>
            <div className="grid grid-cols-3 gap-2 text-xs font-semibold text-counsly-ink">
              <div>Maths: {maths}</div>
              <div>Physics: {physics}</div>
              <div>Chemistry: {chemistry}</div>
            </div>
            <div className="pt-2 border-t border-counsly-line font-bold text-sm text-red-500">
              Calculated Cutoff: {getAggregate().toFixed(2)}
            </div>
          </div>
          <button
            onClick={() => {
              setDenied(false);
              setStep(1);
            }}
            className="button-primary w-full"
          >
            Adjust Marks Inputs
          </button>
        </Surface>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto my-6 md:my-12 space-y-8">
      <div className="text-center mb-8 space-y-3">
        <h1 className="display-title text-center text-4xl md:text-5xl">Configure Workspace</h1>
        <p className="copy text-counsly-muted">Step {step} of 2 — Set up your TNEA counseling parameters.</p>
        <div className="w-48 h-1.5 bg-counsly-soft rounded-full mx-auto overflow-hidden mt-4">
          <div className="bg-counsly-coral h-full transition-all duration-300" style={{ width: `${(step / 2) * 100}%` }} />
        </div>
      </div>

      <Surface className="p-6 md:p-8" tone="paper">
        {step === 1 && (
          <form onSubmit={handleStep1Submit} className="space-y-6">
            <h2 className="font-display text-2xl text-counsly-ink">1. Cutoff Calculation</h2>
            <p className="text-sm leading-relaxed text-counsly-muted">
              Enter your Maths score (out of 100) and Physics/Chemistry scores (out of 50). Counsly computes the TNEA aggregate honestly and uses only official rule-based eligibility checks.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="field-label mb-1">Mathematics</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={maths}
                  onChange={(e) => setMaths(e.target.value === "" ? "" : Number(e.target.value))}
                  required
                  className="field"
                  placeholder="0 - 100"
                />
              </div>
              <div>
                <label className="field-label mb-1">Physics</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={physics}
                  onChange={(e) => setPhysics(e.target.value === "" ? "" : Number(e.target.value))}
                  required
                  className="field"
                  placeholder="0 - 50"
                />
              </div>
              <div>
                <label className="field-label mb-1">Chemistry</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={chemistry}
                  onChange={(e) => setChemistry(e.target.value === "" ? "" : Number(e.target.value))}
                  required
                  className="field"
                  placeholder="0 - 50"
                />
              </div>
            </div>

            {errorMsg && <p className="text-sm font-semibold text-red-500">{errorMsg}</p>}

            <div className="bg-counsly-soft rounded-lg p-4 border border-counsly-line flex items-center justify-between">
              <span className="text-sm font-medium text-counsly-muted">Calculated Cutoff:</span>
              <span className="text-xl font-semibold text-counsly-ink">{getAggregate().toFixed(2)}</span>
            </div>

            <button type="submit" disabled={loading} className="button-primary w-full shadow-md active:scale-98 transition-all flex items-center justify-center gap-2">
              {loading ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <><span>Verify Counseling Eligibility</span><ChevronRight className="w-4.5 h-4.5" /></>}
            </button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleStep2Submit} className="space-y-6">
            <h2 className="font-display text-2xl text-counsly-ink">2. Community & Record Setup</h2>
            <p className="text-sm leading-relaxed text-counsly-muted">
              Select your community category and provide TNEA registration details to calibrate the rule-based college exploration flows.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"].map((comm) => (
                <button
                  key={comm}
                  type="button"
                  onClick={() => setCommunity(comm)}
                  className={`py-2.5 rounded-lg text-sm font-semibold border transition ${
                    community === comm
                      ? "border-counsly-coral bg-counsly-coral text-white shadow-sm"
                      : "border-counsly-line hover:border-counsly-coral bg-counsly-canvas text-counsly-ink"
                  }`}
                >
                  {comm}
                </button>
              ))}
            </div>

            <div className="space-y-2">
              <label className="field-label">Have a Roll Number? (Optional)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. 984523"
                  value={rollNumber}
                  onChange={(e) => setRollNumber(e.target.value)}
                  className="field flex-1"
                />
                <button
                  type="button"
                  onClick={handleVerifyRoll}
                  className="button-secondary min-h-11 px-4"
                >
                  Verify
                </button>
              </div>
              {rollVerified && (
                <p className="text-xs font-medium text-counsly-muted flex items-center gap-1.5 mt-1 bg-counsly-soft/50 p-2.5 rounded-lg border border-counsly-line animate-fade-in">
                  <UserCheck className="w-4 h-4 text-green-600 shrink-0" />
                  <span>Official-rank workflow will automatically activate once the registry confirms this roll number.</span>
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="field-label mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  required
                  className="field"
                />
              </div>
              <div>
                <label className="field-label mb-1">TNEA General Rank</label>
                <input
                  type="number"
                  placeholder="e.g. 1524"
                  value={generalRank}
                  onChange={(e) => setGeneralRank(e.target.value === "" ? "" : Number(e.target.value))}
                  className="field"
                />
              </div>
              <div>
                <label className="field-label mb-1">Community Rank</label>
                <input
                  type="number"
                  placeholder="e.g. 341"
                  value={communityRank}
                  onChange={(e) => setCommunityRank(e.target.value === "" ? "" : Number(e.target.value))}
                  className="field"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="button-primary w-full shadow-md active:scale-98 transition-all flex items-center justify-center gap-2">
              {loading ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <><Shield className="w-4 h-4" /><span>Build 2027 Workspace</span></>}
            </button>
          </form>
        )}
      </Surface>
    </div>
  );
}

export default function Onboarding() {
  return <OnboardingWizard />;
}
