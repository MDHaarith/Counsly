"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { postJson } from "@/lib/api";

export default function MarksPage() {
  const router = useRouter();
  const [maths, setMaths] = useState("");
  const [physics, setPhysics] = useState("");
  const [chemistry, setChemistry] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const total = Number(maths || 0) + Number(physics || 0) / 2 + Number(chemistry || 0) / 2;

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      await postJson("/api/onboarding/marks", {
        maths_mark: Number(maths),
        physics_mark: Number(physics),
        chemistry_mark: Number(chemistry),
      });
      router.push("/onboarding/details");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save marks.");
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-serif text-[30px] font-medium leading-tight">Enter your marks</h1>
        <p className="mt-2 text-sm leading-relaxed text-olive-gray">Use your TNEA cutoff subjects. Counsly uses range-based guidance, not exact rank prediction.</p>
      </div>
      <div className="grid gap-3">
        <Input label="Maths" value={maths} onChange={(e) => setMaths(e.target.value)} inputMode="numeric" type="number" />
        <Input label="Physics" value={physics} onChange={(e) => setPhysics(e.target.value)} inputMode="numeric" type="number" />
        <Input label="Chemistry" value={chemistry} onChange={(e) => setChemistry(e.target.value)} inputMode="numeric" type="number" />
      </div>
      <Card>
        <p className="text-sm text-olive-gray">Estimated cutoff</p>
        <p className="mt-1 font-mono text-3xl font-semibold">{total.toFixed(1)}/200</p>
        {total > 0 && total < 90 && <p className="mt-2 text-sm text-error-crimson">Below 90/200, recommendation and choice guidance stays locked. You can still browse colleges.</p>}
      </Card>
      {error && <p className="text-sm text-error-crimson">{error}</p>}
      <Button onClick={submit} disabled={saving || !maths || !physics || !chemistry}>{saving ? "Saving..." : "Continue"}</Button>
    </div>
  );
}
