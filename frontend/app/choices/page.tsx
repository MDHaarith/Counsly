"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  closestCenter,
  DndContext,
  DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Download, FileDown, GripVertical, Plus, Save, UploadCloud, FileStack } from "lucide-react";

import { Badge, PageHeader, Surface, EmptyState, StatusToast } from "@/components/ui";
import { FeatureGate } from "@/components/feature-gate";
import { useApp } from "@/app/AppContext";
import {
  createChoiceSnapshot,
  fetchChoiceSnapshots,
  fetchChoices,
  reorderChoices,
  restoreChoiceSnapshot,
  updateChoice,
  uploadChoiceCsv,
} from "@/lib/api.mjs";
import { buildChoiceExportModel, choiceExportFilename } from "@/lib/choice-export.mjs";
import { ChoiceDraft, FitBand, choiceDrafts, toneForBand, cleanCollegeName } from "@/lib/product";
import { ChoiceItem, ChoiceRow } from "@/components/choices/ChoiceItem";

type SnapshotRecord = { id?: string; itemCount?: number; rows?: ChoiceRow[]; title: string };

function resequence(rows: ChoiceRow[]) {
  return rows.map((row, index) => ({ ...row, priority: index + 1 }));
}

function ChoicesContent() {
  const { user } = useApp();
  const [choices, setChoices] = useState<ChoiceRow[]>(() =>
    choiceDrafts.map((choice) => ({ ...choice, id: `${choice.code}-${choice.branchCode}`, manual: false })),
  );
  const [activeId, setActiveId] = useState(choices[0]?.id ?? "");
  const [snapshot, setSnapshot] = useState("No snapshot saved in this session.");
  const [snapshots, setSnapshots] = useState<SnapshotRecord[]>([]);
  const [pendingImport, setPendingImport] = useState<ChoiceRow[]>([]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [toast, setToast] = useState<{ message: string; tone: "success" | "error" | "default" } | null>(null);
  
  const fileRef = useRef<HTMLInputElement>(null);
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const activeChoice = useMemo(() => choices.find((choice) => choice.id === activeId), [activeId, choices]);

  const showToast = (message: string, tone: "success" | "error" | "default" = "default") => {
    setToast({ message, tone });
  };

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  useEffect(() => {
    let active = true;
    Promise.all([fetchChoices(), fetchChoiceSnapshots()])
      .then(([rows, saved]) => {
        if (!active) return;
        if (rows.length) {
          setChoices(rows);
          setActiveId(rows[0].id);
        }
        setSnapshots(saved.map((item: { id: string; item_count: number; title: string }) => ({
          id: item.id,
          itemCount: item.item_count,
          title: item.title,
        })));
        showToast(rows.length ? "Choices loaded." : "Workspace list is empty.", "success");
      })
      .catch(() => showToast("Working in local preview mode.", "default"));

    return () => {
      active = false;
    };
  }, []);

  const changeChoice = (id: string, next: Partial<ChoiceRow>) => {
    setChoices((rows) => rows.map((row) => (row.id === id ? { ...row, ...next } : row)));
  };

  const syncOrder = async (rows: ChoiceRow[]) => {
    try {
      await reorderChoices(rows);
      showToast(`Filing order saved to cloud.`, "success");
    } catch {
      showToast("API unreachable. Filing order saved locally.", "error");
    }
  };

  const persistChoice = async (choice: ChoiceRow) => {
    if (!choice.backendId) return;
    try {
      await updateChoice(choice);
      showToast("Metadata saved to cloud.", "success");
    } catch {
      showToast("Notes saved locally (sync pending).", "default");
    }
  };

  const jumpChoice = (id: string, target: number) => {
    if (!target || target < 1 || target > choices.length) return;
    const from = choices.findIndex((row) => row.id === id);
    const next = resequence(arrayMove(choices, from, target - 1));
    setChoices(next);
    void syncOrder(next);
  };

  const onDragEnd = (event: DragEndEvent) => {
    if (!event.over || event.active.id === event.over.id) return;
    const from = choices.findIndex((row) => row.id === event.active.id);
    const to = choices.findIndex((row) => row.id === event.over?.id);
    const next = resequence(arrayMove(choices, from, to));
    setChoices(next);
    void syncOrder(next);
  };

  const saveSnapshot = async () => {
    const title = window.prompt("Snapshot title", `Round list ${snapshots.length + 1}`)?.trim();
    if (!title) return;
    try {
      const saved = await createChoiceSnapshot(title);
      setSnapshots((current) => [{ id: saved.id, itemCount: saved.item_count, title: saved.title }, ...current]);
      setSnapshot(`${title} saved to the workspace with ${saved.item_count} rows.`);
      showToast(`Snapshot "${title}" saved.`, "success");
    } catch {
      setSnapshots((current) => [{ title, rows: choices.map((choice) => ({ ...choice })) }, ...current]);
      setSnapshot(`${title} saved locally at ${new Date().toLocaleTimeString()}.`);
      showToast(`Snapshot "${title}" saved locally.`, "success");
    }
  };

  const exportCsv = () => {
    const rows = [
      "priority,college_code,branch_code,category,notes",
      ...choices.map((choice) =>
        [choice.priority, choice.code, choice.branchCode, choice.fitBand, `"${choice.notes.replaceAll('"', '""')}"`].join(","),
      ),
    ];
    const href = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = href;
    link.download = "counsly-choice-list.csv";
    link.click();
    URL.revokeObjectURL(href);
  };

  const readStudentContext = () => {
    try {
      const stored = window.localStorage.getItem("counsly_student_context");
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  };

  const exportPdf = async () => {
    const exportedAt = new Date();
    const model = buildChoiceExportModel({
      choices,
      exportedAt,
      student: {
        ...readStudentContext(),
        name: readStudentContext().name || user?.name || "Counsly student",
      },
    });
    const { jsPDF } = await import("jspdf");
    const doc = new jsPDF({ unit: "pt", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 44;
    let y = 48;

    doc.setFillColor(250, 247, 241);
    doc.rect(0, 0, pageWidth, 140, "F");
    doc.setTextColor(31, 30, 27);
    doc.setFont("times", "bold");
    doc.setFontSize(24);
    doc.text(model.title, margin, y);
    y += 28;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    model.meta.forEach((line: string) => {
      doc.text(line, margin, y);
      y += 15;
    });

    y = 166;
    const columns = [margin, 76, 186, 300, 386];
    const headers = ["#", "College", "Branch", "Band", "Notes"];
    doc.setFillColor(31, 30, 27);
    doc.roundedRect(margin, y - 18, pageWidth - margin * 2, 26, 8, 8, "F");
    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    headers.forEach((header, index) => doc.text(header, columns[index], y));
    y += 22;

    doc.setFont("helvetica", "normal");
    doc.setTextColor(55, 53, 47);
    model.rows.forEach((row: string[], index: number) => {
      if (y > 728) {
        doc.addPage();
        y = 54;
      }
      if (index % 2 === 0) {
        doc.setFillColor(252, 250, 246);
        doc.rect(margin, y - 14, pageWidth - margin * 2, 32, "F");
      }
      doc.text(row[0], columns[0], y);
      doc.text(doc.splitTextToSize(row[1], 96), columns[1], y);
      doc.text(doc.splitTextToSize(row[2], 102), columns[2], y);
      doc.text(row[3], columns[3], y);
      doc.text(doc.splitTextToSize(row[4] || "-", 148).slice(0, 2), columns[4], y);
      y += 34;
    });

    if (y > 704) {
      doc.addPage();
      y = 54;
    }
    doc.setDrawColor(226, 219, 207);
    doc.line(margin, y, pageWidth - margin, y);
    y += 20;
    doc.setFontSize(9);
    doc.setTextColor(112, 105, 95);
    doc.text(doc.splitTextToSize(model.disclaimer, pageWidth - margin * 2), margin, y);
    doc.save(choiceExportFilename(exportedAt));
  };

  const importCsv = async (event: FormEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    if (!file) return;
    setPendingFile(file);
    const lines = (await file.text()).split(/\r?\n/).slice(1).filter(Boolean);
    const imported = lines.map((line, index) => {
      const [priority, code, branchCode, fitBand, note] = line.split(",");
      const source = choiceDrafts.find((choice) => choice.code === code) ?? choiceDrafts[index % choiceDrafts.length];
      return {
        ...source,
        id: `${code || source.code}-${branchCode || source.branchCode}-${index}`,
        code: code || source.code,
        branchCode: branchCode || source.branchCode,
        fitBand: (fitBand as FitBand) || source.fitBand,
        manual: true,
        notes: note?.replaceAll('"', "") || source.notes,
        priority: Number(priority) || choices.length + index + 1,
      };
    });
    setPendingImport(resequence(imported).slice(0, 300));
  };

  return (
    <div className="space-y-8 relative">
        {toast && (
          <div className="fixed bottom-24 right-6 z-50 animate-slide-up">
            <StatusToast message={toast.message} tone={toast.tone} />
          </div>
        )}

        <PageHeader
          actions={
            <>
              <button className="button-secondary" onClick={() => fileRef.current?.click()} type="button">
                <UploadCloud className="h-4 w-4" /> Import CSV
              </button>
              <button className="button-secondary" onClick={exportCsv} type="button">
                <Download className="h-4 w-4" /> Export CSV
              </button>
              <button className="button-secondary" onClick={exportPdf} type="button">
                <FileDown className="h-4 w-4" /> Export PDF
              </button>
              <button className="button-primary" onClick={saveSnapshot} type="button">
                <Save className="h-4 w-4" /> Save snapshot
              </button>
            </>
          }
          description="Manage, reorder, and snapshot your choice filing list. Export as CSV or official PDF."
          eyebrow="Primary surface"
          title="Choice filing workspace"
        />
        <input accept=".csv,text/csv" className="hidden" onInput={importCsv} ref={fileRef} type="file" />

        {choices.length === 0 ? (
          <Surface className="p-10 flex flex-col items-center justify-center min-h-[350px]" tone="paper">
            <EmptyState
              icon={<FileStack className="h-8 w-8" />}
              title="Your Choice List is Empty"
              description="Browse the College Explorer or Recommendations to find colleges and add them to your filing workspace."
              action={
                <Link href="/explore" className="button-primary mt-4">
                  <Plus className="h-4 w-4" /> Browse Colleges
                </Link>
              }
            />
          </Surface>
        ) : (
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
            <Surface className="space-y-3 p-4 md:p-5" tone="paper">
              <DndContext collisionDetection={closestCenter} onDragEnd={onDragEnd} sensors={sensors}>
                <SortableContext items={choices.map((choice) => choice.id)} strategy={verticalListSortingStrategy}>
                  <div className="space-y-3">
                    {choices.map((choice) => (
                      <ChoiceItem
                        activeId={activeId}
                        choice={choice}
                        key={choice.id}
                        onChange={changeChoice}
                        onJump={jumpChoice}
                        onPersist={persistChoice}
                        onSelect={setActiveId}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            </Surface>

            <div className="space-y-4">
              <Surface className="space-y-4 p-5 animate-fade-in" tone="soft">
                <Badge tone="neutral">Active row</Badge>
                {activeChoice ? (
                  <>
                    <h2 className="font-display text-3xl text-counsly-ink">{cleanCollegeName(activeChoice.name)}</h2>
                    <p className="text-sm leading-6 text-counsly-body">{activeChoice.notes || "No custom notes entered for this choice."}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <span className="rounded-lg bg-counsly-canvas p-3 text-counsly-muted">Cutoff <strong className="block font-mono text-counsly-ink mt-1 text-lg">{activeChoice.cutoff}</strong></span>
                      <span className="rounded-lg bg-counsly-canvas p-3 text-counsly-muted">Seats <strong className="block font-mono text-counsly-ink mt-1 text-lg">{activeChoice.seats}</strong></span>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-counsly-muted">Select a college to view details.</p>
                )}
              </Surface>
              
              <Surface className="space-y-3 p-5" tone="soft">
                <p className="eyebrow">Snapshot status</p>
                <p className="text-sm leading-6 text-counsly-body">{snapshot}</p>
                <div className="space-y-2">
                  {snapshots.map((item) => (
                    <button
                      className="flex w-full items-center justify-between rounded-lg border border-counsly-line bg-counsly-canvas p-3 text-left text-sm text-counsly-body hover:border-counsly-coral transition"
                      key={item.title}
                      onClick={async () => {
                        if (item.id) {
                          try {
                            await restoreChoiceSnapshot(item.id);
                            const rows = await fetchChoices();
                            setChoices(rows);
                            setActiveId(rows[0]?.id ?? "");
                            setSnapshot(`${item.title} restored from the workspace.`);
                            showToast(`${item.title} restored.`, "success");
                            return;
                          } catch {
                            setSnapshot(`${item.title} could not be restored.`);
                            showToast("Error restoring snapshot.", "error");
                          }
                        }
                        if (item.rows) {
                          setChoices(item.rows.map((row) => ({ ...row })));
                          setSnapshot(`${item.title} restored as current list.`);
                          showToast(`${item.title} restored.`, "success");
                        }
                      }}
                      type="button"
                    >
                      <span>{item.title}</span>
                      <span className="text-xs text-counsly-muted">{item.itemCount ? `${item.itemCount} rows` : "Restore"}</span>
                    </button>
                  ))}
                </div>
                <Link className="button-secondary w-full" href="/explore">
                  <Plus className="h-4 w-4" /> Add college from explorer
                </Link>
              </Surface>
            </div>
          </div>
        )}

        {pendingImport.length > 0 && (
          <Surface className="space-y-4 p-5" tone="soft">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
              <div>
                <p className="eyebrow">CSV import preview</p>
                <h2 className="font-display text-3xl text-counsly-ink">{pendingImport.length} rows ready to append</h2>
              </div>
              <div className="flex gap-2">
                <button className="button-secondary" onClick={() => setPendingImport([])} type="button">Cancel</button>
                <button
                  className="button-primary"
                  onClick={async () => {
                    if (pendingFile) {
                      try {
                        await uploadChoiceCsv(pendingFile);
                        const rows = await fetchChoices();
                        setChoices(rows);
                        setActiveId(rows[0]?.id ?? "");
                        showToast(`Imported ${pendingImport.length} rows.`, "success");
                        setPendingImport([]);
                        setPendingFile(null);
                        return;
                      } catch {
                        showToast("API error. Applied preview locally.", "default");
                      }
                    }
                    setChoices((rows) => resequence([...rows, ...pendingImport]).slice(0, 300));
                    setPendingImport([]);
                    setPendingFile(null);
                  }}
                  type="button"
                >
                  Apply import
                </button>
              </div>
            </div>
            <div className="grid gap-2 md:grid-cols-2">
              {pendingImport.slice(0, 4).map((choice) => (
                <p className="rounded-lg bg-counsly-canvas p-3 text-sm text-counsly-body" key={choice.id}>
                  {choice.priority}. {choice.code} {choice.branchCode} <span className="text-counsly-muted">({choice.fitBand})</span>
                </p>
              ))}
            </div>
          </Surface>
        )}

        <div className="sticky bottom-24 z-20 flex gap-2 rounded-2xl border border-counsly-line bg-counsly-canvas/95 p-2 shadow-[0_18px_45px_rgba(20,20,19,0.14)] backdrop-blur md:hidden">
          <Link className="button-secondary min-w-0 flex-1 px-3 text-center flex items-center justify-center" href="/explore">
            Add
          </Link>
          <button className="button-primary min-w-0 flex-1 px-3" onClick={saveSnapshot} type="button">
            Snapshot
          </button>
          <button className="button-secondary min-w-0 flex-1 px-3" onClick={exportPdf} type="button">
            PDF
          </button>
        </div>
      </div>
  );
}

export default function ChoicesPage() {
  return (
    <FeatureGate>
      <ChoicesContent />
    </FeatureGate>
  );
}
