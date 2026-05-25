"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "../AppContext";
import { AlertTriangle, ChevronRight, Shield, UserCheck } from "lucide-react";
import confetti from "canvas-confetti";

import { runOnboarding } from "@/lib/api.mjs";
import { trackFunnelEvent } from "@/lib/analytics.mjs";

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
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [denied, setDenied] = useState(false);
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
    try {
      await runOnboarding({
        maths: m,
        physics: p,
        chemistry: c,
        preferred_branches: [],
      });
      setStep(2);
    } catch {
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteOnboarding = () => {
    setLoading(true);
    setTimeout(() => {
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
      <div className="max-w-md mx-auto my-12 glass-card rounded-2xl p-8 border-red-200 shadow-xl text-center space-y-6 animate-slide-up">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-500 mx-auto">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-counsly-primary tracking-tight">Cutoff Eligibility Denied</h2>
        <p className="text-sm font-semibold text-gray-500">
          Under current TNEA guidelines, an aggregate score below <span className="text-red-500 font-extrabold">78.0 / 200</span> does not meet the eligibility gate threshold.
        </p>
        <div className="bg-red-50 rounded-lg p-4 border border-red-100 text-left">
          <span className="block text-xs font-bold text-red-600 mb-1">Your Metrics:</span>
          <div className="grid grid-cols-3 gap-2 text-xs font-semibold text-counsly-slate">
            <div>Maths: {maths}</div>
            <div>Physics: {physics}</div>
            <div>Chemistry: {chemistry}</div>
          </div>
          <div className="mt-3 pt-3 border-t border-red-100 font-extrabold text-sm text-red-600">
            Calculated Cutoff: {getAggregate().toFixed(2)}
          </div>
        </div>
        <button
          onClick={() => {
            setDenied(false);
            setStep(1);
          }}
          className="w-full bg-counsly-primary text-white py-3 rounded-lg font-bold text-sm hover:bg-counsly-slate transition-all"
        >
          Adjust Marks Inputs
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto my-6 md:my-12">
      <div className="text-center mb-8 space-y-2">
        <h1 className="text-3xl font-black text-counsly-primary tracking-tight">Configure Workspace</h1>
        <p className="text-sm font-semibold text-gray-400">Step {step} of 2 — Setup counseling criteria parameters</p>
        <div className="w-48 h-1 bg-gray-200 rounded-full mx-auto overflow-hidden">
          <div className="bg-counsly-coral h-full transition-all duration-300" style={{ width: `${(step / 2) * 100}%` }} />
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6 md:p-8 shadow-md">
        {step === 1 && (
          <form onSubmit={handleStep1Submit} className="space-y-6">
            <h2 className="text-xl font-extrabold text-counsly-primary">1. Cutoff Calculation</h2>
            <p className="text-xs text-gray-500 font-semibold">
              Enter Maths out of 100 and Physics/Chemistry out of 50. Counsly computes the TNEA aggregate honestly and uses only rule-based eligibility checks in the 2027 version.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-counsly-slate mb-1">Mathematics</label>
                <input type="number" min="0" max="100" value={maths} onChange={(e) => setMaths(e.target.value === "" ? "" : Number(e.target.value))} required className="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm font-semibold focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-bold text-counsly-slate mb-1">Physics</label>
                <input type="number" min="0" max="50" value={physics} onChange={(e) => setPhysics(e.target.value === "" ? "" : Number(e.target.value))} required className="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm font-semibold focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-bold text-counsly-slate mb-1">Chemistry</label>
                <input type="number" min="0" max="50" value={chemistry} onChange={(e) => setChemistry(e.target.value === "" ? "" : Number(e.target.value))} required className="w-full px-4 py-2 rounded-lg border border-gray-200 text-sm font-semibold focus:outline-none" />
              </div>
            </div>

            {errorMsg && <p className="text-xs font-bold text-red-500">{errorMsg}</p>}

            <div className="bg-counsly-cream rounded-lg p-4 border border-gray-100 flex items-center justify-between">
              <span className="text-xs font-bold text-counsly-slate">Calculated Cutoff:</span>
              <span className="text-base font-extrabold text-counsly-primary">{getAggregate().toFixed(2)}</span>
            </div>

            <button type="submit" disabled={loading} className="w-full bg-counsly-primary text-white py-3 rounded-lg font-bold text-sm shadow-md hover:bg-counsly-slate active:scale-98 transition-all flex items-center justify-center gap-2">
              {loading ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <><span>Verify Counseling Eligibility</span><ChevronRight className="w-4.5 h-4.5" /></>}
            </button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleStep2Submit} className="space-y-6">
            <h2 className="text-xl font-extrabold text-counsly-primary">2. Community and Record Setup</h2>
            <p className="text-xs text-gray-500 font-semibold">
              Save the district and category context used by the rule-based college exploration flows.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"].map((comm) => (
                <button
                  key={comm}
                  type="button"
                  onClick={() => setCommunity(comm)}
                  className={`py-3 rounded-lg text-sm font-bold border transition-all ${community === comm ? "border-counsly-primary bg-counsly-primary text-white shadow-sm" : "border-gray-200 hover:border-counsly-primary bg-white text-counsly-primary"}`}
                >
                  {comm}
                </button>
              ))}
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-bold text-counsly-slate">Have a Roll Number? (Optional)</label>
              <div className="flex gap-2">
                <input type="text" placeholder="e.g. 984523" value={rollNumber} onChange={(e) => setRollNumber(e.target.value)} className="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 text-sm font-semibold focus:outline-none" />
                <button type="button" onClick={() => setRollVerified(true)} className="bg-counsly-slate text-white px-4 rounded-lg text-xs font-bold shadow-sm">
                  Mark as Verified
                </button>
              </div>
              {rollVerified && (
                <p className="text-xs font-bold text-counsly-safe flex items-center gap-1">
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>Official-rank workflow can start once the counseling registry confirms this roll number.</span>
                </p>
              )}
            </div>

            <button type="submit" disabled={loading} className="w-full bg-counsly-primary text-white py-3 rounded-lg font-bold text-sm shadow-md hover:bg-counsly-slate active:scale-98 transition-all flex items-center justify-center gap-2">
              {loading ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <><Shield className="w-4 h-4" /><span>Build 2027 Workspace</span></>}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function Onboarding() {
  return <OnboardingWizard />;
}
