"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiClient, postJson } from "@/lib/api";
import type { SafetyLabel } from "@/types";

interface ChoiceItem {
  id: string;
  priority: number;
  college_code: string;
  college_name: string | null;
  branch_code: string;
  branch_name: string | null;
  district: string | null;
  system_category: SafetyLabel | null;
  manual_category: SafetyLabel | null;
  notes: string | null;
}

interface ChoicesPayload {
  items: ChoiceItem[];
  limit: number;
  paid: boolean;
}

export function ChoicesClient({ initialData }: { initialData: ChoicesPayload | null }) {
  const [data, setData] = useState<ChoicesPayload | null>(initialData);
  const [error, setError] = useState<string | null>(null);
  const [moving, setMoving] = useState<string | null>(null);
  const [collegeCode, setCollegeCode] = useState("");
  const [branchCode, setBranchCode] = useState("");
  const [notes, setNotes] = useState("");
  const [manualCategory, setManualCategory] = useState<SafetyLabel | "">("");
  const [saving, setSaving] = useState(false);

  async function move(choice: ChoiceItem, priority: string) {
    const next = Number(priority);
    if (!next || next === choice.priority) return;
    setMoving(choice.id);
    try {
      setData(await postJson<ChoicesPayload>(`/api/choices/${choice.id}/move`, { priority: next }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not move choice.");
    } finally {
      setMoving(null);
    }
  }

  async function addChoice() {
    if (!collegeCode.trim() || !branchCode.trim()) {
      setError("College code and branch code are required.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        college_code: collegeCode.trim().toUpperCase(),
        branch_code: branchCode.trim().toUpperCase(),
        notes: notes.trim() || null,
        manual_category: manualCategory || null,
      };
      setData(await postJson<ChoicesPayload>("/api/choices", payload));
      setCollegeCode("");
      setBranchCode("");
      setNotes("");
      setManualCategory("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add choice.");
    } finally {
      setSaving(false);
    }
  }

  async function updateChoice(choice: ChoiceItem, patch: { notes?: string | null; manual_category?: SafetyLabel | null }) {
    setMoving(choice.id);
    try {
      setData(
        await apiClient<ChoicesPayload>(`/api/choices/${choice.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            notes: patch.notes === undefined ? choice.notes : patch.notes,
            manual_category: patch.manual_category === undefined ? choice.manual_category : patch.manual_category,
          }),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update choice.");
    } finally {
      setMoving(null);
    }
  }

  async function deleteChoice(choice: ChoiceItem) {
    setMoving(choice.id);
    try {
      setData(await apiClient<ChoicesPayload>(`/api/choices/${choice.id}`, { method: "DELETE" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete choice.");
    } finally {
      setMoving(null);
    }
  }

  async function exportChoices() {
    if (!data) return;
    try {
      const { jsPDF } = await import("jspdf");
      const doc = new jsPDF();
      const margin = 14;
      let y = 18;
      doc.setFont("times", "normal");
      doc.setFontSize(18);
      doc.text("Counsly choice list", margin, y);
      y += 8;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      doc.text(`${data.items.length}/${data.limit} active choices`, margin, y);
      y += 10;
      data.items.forEach((choice) => {
        const lines = doc.splitTextToSize(
          `${choice.priority}. ${choice.college_name ?? choice.college_code} - ${choice.branch_name ?? choice.branch_code} (${choice.district ?? "District pending"})`,
          180,
        );
        if (y + lines.length * 5 + 8 > 285) {
          doc.addPage();
          y = 18;
        }
        doc.setFont("helvetica", "bold");
        doc.text(lines, margin, y);
        y += lines.length * 5;
        doc.setFont("helvetica", "normal");
        const meta = [choice.manual_category ?? choice.system_category, choice.notes].filter(Boolean).join(" | ");
        if (meta) {
          const metaLines = doc.splitTextToSize(meta, 180);
          doc.text(metaLines, margin + 4, y);
          y += metaLines.length * 5;
        }
        y += 4;
      });
      doc.save("counsly-choice-list.pdf");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not export PDF.");
    }
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button variant="secondary" className="w-auto flex-1" onClick={exportChoices} disabled={data.items.length === 0}>
          Export PDF
        </Button>
        <Button variant="ghost" className="w-auto flex-1" onClick={() => void apiClient<ChoicesPayload>("/api/choices").then(setData)}>
          Refresh
        </Button>
      </div>

      {error && (
        <Card>
          <p className="text-sm text-error-crimson">{error}</p>
        </Card>
      )}

      {data.items.length === 0 && (
        <Card>
          <h2 className="font-serif text-lg font-medium">No choices yet</h2>
          <p className="mt-1 text-sm text-olive-gray">Add colleges from recommendations or explore, then reorder them here.</p>
        </Card>
      )}

      <div className="grid gap-3">
        {data.items.map((choice) => (
          <Card key={choice.id}>
            <div className="flex items-start gap-3">
              <input
                aria-label="Priority"
                defaultValue={choice.priority}
                inputMode="numeric"
                onBlur={(e) => move(choice, e.target.value)}
                className="h-12 w-14 rounded-xl border border-border-cream bg-white text-center font-mono text-base font-semibold text-anthracite outline-none focus:border-focus-blue focus:shadow-focus-ring"
              />
              <div className="min-w-0 flex-1">
                <h2 className="font-serif text-lg font-medium leading-snug">{choice.college_name ?? choice.college_code}</h2>
                <p className="mt-1 text-sm text-olive-gray">
                  {choice.branch_name ?? choice.branch_code} · {choice.district ?? "District pending"}
                </p>
                <div className="mt-2 flex gap-2">
                  {choice.manual_category && <Badge variant={choice.manual_category}>manual {choice.manual_category}</Badge>}
                  {choice.system_category && <Badge variant={choice.system_category}>{choice.system_category}</Badge>}
                </div>
              </div>
            </div>
            {choice.notes && <p className="mt-3 text-sm leading-relaxed text-olive-gray">{choice.notes}</p>}
            <div className="mt-3 grid gap-2">
              <Input
                label="Notes"
                defaultValue={choice.notes ?? ""}
                onBlur={(e) => updateChoice(choice, { notes: e.target.value.trim() || null })}
              />
              <div className="flex gap-2">
                {(["safe", "moderate", "ambitious"] as SafetyLabel[]).map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => updateChoice(choice, { manual_category: choice.manual_category === category ? null : category })}
                    className={[
                      "min-h-12 flex-1 rounded-xl border px-2 text-xs font-medium capitalize",
                      choice.manual_category === category
                        ? "border-anthracite bg-warm-sand text-anthracite"
                        : "border-border-cream bg-ivory text-olive-gray",
                    ].join(" ")}
                  >
                    {category}
                  </button>
                ))}
                <Button variant="ghost" className="w-auto px-3 text-error-crimson" onClick={() => deleteChoice(choice)}>
                  Remove
                </Button>
              </div>
            </div>
            {moving === choice.id && <p className="mt-2 text-xs text-stone-gray">Saving new position...</p>}
          </Card>
        ))}
      </div>

      {!data.paid && data.items.length >= data.limit && (
        <Card variant="featured">
          <p className="text-sm text-olive-gray">Free choices are limited to {data.limit} rows.</p>
          <Link href="/subscribe?from=choices">
            <Button className="mt-3">Unlock Full Access</Button>
          </Link>
        </Card>
      )}

      <Card>
        <h2 className="font-serif text-lg font-medium">Quick add</h2>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <Input label="College code" value={collegeCode} onChange={(e) => setCollegeCode(e.target.value)} />
          <Input label="Branch code" value={branchCode} onChange={(e) => setBranchCode(e.target.value)} />
        </div>
        <div className="mt-3">
          <Input label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <div className="mt-3 flex gap-2">
          {(["safe", "moderate", "ambitious"] as SafetyLabel[]).map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setManualCategory(manualCategory === category ? "" : category)}
              className={[
                "min-h-12 flex-1 rounded-xl border px-2 text-xs font-medium capitalize",
                manualCategory === category ? "border-anthracite bg-warm-sand text-anthracite" : "border-border-cream bg-ivory text-olive-gray",
              ].join(" ")}
            >
              {category}
            </button>
          ))}
        </div>
        <Button className="mt-3" onClick={addChoice} disabled={saving}>
          {saving ? "Adding" : "Add to list"}
        </Button>
      </Card>
    </div>
  );
}
