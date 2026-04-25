"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { postJson } from "@/lib/api";
import type { Board, Community } from "@/types";

const communities: Community[] = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"];
const boards: Board[] = ["State", "CBSE", "ICSE"];

export default function DetailsPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [district, setDistrict] = useState("");
  const [homeDistrict, setHomeDistrict] = useState("");
  const [community, setCommunity] = useState<Community>("BC");
  const [board, setBoard] = useState<Board>("State");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      await postJson("/api/onboarding/details", {
        full_name: fullName,
        board,
        district,
        home_district: homeDistrict,
        community_quota: community,
      });
      router.push("/onboarding/rank");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save details.");
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-serif text-[30px] font-medium leading-tight">Your counselling details</h1>
        <p className="mt-2 text-sm leading-relaxed text-olive-gray">Community and district affect cutoffs, recommendations, and nearby help later.</p>
      </div>
      <div className="grid gap-3">
        <Input label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <Input label="Current district" value={district} onChange={(e) => setDistrict(e.target.value)} />
        <Input label="Home district" value={homeDistrict} onChange={(e) => setHomeDistrict(e.target.value)} />
      </div>
      <Card>
        <label className="text-sm font-medium text-olive-gray">Community</label>
        <div className="mt-2 grid grid-cols-4 gap-2">
          {communities.map((item) => (
            <button key={item} onClick={() => setCommunity(item)} className={["h-11 rounded-lg text-sm font-medium", community === item ? "bg-anthracite text-ivory" : "bg-surface-alt text-olive-gray"].join(" ")}>{item}</button>
          ))}
        </div>
      </Card>
      <Card>
        <label className="text-sm font-medium text-olive-gray">Board</label>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {boards.map((item) => (
            <button key={item} onClick={() => setBoard(item)} className={["h-11 rounded-lg text-sm font-medium", board === item ? "bg-anthracite text-ivory" : "bg-surface-alt text-olive-gray"].join(" ")}>{item}</button>
          ))}
        </div>
      </Card>
      {error && <p className="text-sm text-error-crimson">{error}</p>}
      <Button onClick={submit} disabled={saving || !fullName || !district || !homeDistrict}>{saving ? "Saving..." : "See rank band"}</Button>
    </div>
  );
}
