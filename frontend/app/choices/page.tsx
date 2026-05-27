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
import { Download, FileDown, GripVertical, Plus, Save, UploadCloud } from "lucide-react";

import { Badge, PageHeader, Surface } from "@/components/ui";
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

type ChoiceRow = ChoiceDraft & { backendId?: number; id: string; manual: boolean };
type SnapshotRecord = { id?: string; itemCount?: number; rows?: ChoiceRow[]; title: string };

function resequence(rows: ChoiceRow[]) {
  return rows.map((row, index) => ({ ...row, priority: index + 1 }));
}

function ChoiceItem({
  activeId,
  choice,
  onChange,
  onJump,
  onPersist,
  onSelect,
}: {
  activeId: string;
  choice: ChoiceRow;
  onChange: (id: string, next: Partial<ChoiceRow>) => void;
  onJump: (id: string, target: number) => void;
  onPersist: (choice: ChoiceRow) => void;
  onSelect: (id: string) => void;
}) {
  const sortable = useSortable({ id: choice.id });

  return (
    <article
      className={`rounded-xl border p-4 transition ${
        activeId === choice.id
          ? "border-counsly-coral bg-counsly-card"
          : "border-counsly-line bg-counsly-canvas"
      }`}
      ref={sortable.setNodeRef}
      style={{
        transform: CSS.Transform.toString(sortable.transform),
        transition: sortable.transition,
      }}
    >
      <div className="grid gap-4 lg:grid-cols-[44px_minmax(0,1fr)_170px_220px]">
        <button
          aria-label={`Reorder ${cleanCollegeName(choice.name)}`}
          className="hidden h-11 w-11 cursor-grab items-center justify-center rounded-lg border border-counsly-line text-counsly-muted lg:flex"
          type="button"
          {...sortable.attributes}
          {...sortable.listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <button className="space-y-2 text-left" onClick={() => onSelect(choice.id)} type="button">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="dark">{choice.priority.toString().padStart(2, "0")}</Badge>
            <Badge>{choice.code}</Badge>
            <Badge tone={toneForBand(choice.fitBand)}>{choice.fitBand}</Badge>
            {choice.manual && <Badge tone="warning">Manually set</Badge>}
          </div>
          <div>
            <h2 className="text-base font-semibold text-counsly-ink">{cleanCollegeName(choice.name)}</h2>
            <p className="text-sm leading-6 text-counsly-body">
              {choice.branchName} ({choice.branchCode})
            </p>
          </div>
        </button>
        <label className="field-label">
          Jump to
          <input
            className="field font-mono"
            max={300}
            min={1}
            onChange={(event) => onJump(choice.id, Number(event.target.value))}
            type="number"
            value={choice.priority}
          />
        </label>
        <label className="field-label">
          Category
          <select
            className="field"
            onChange={(event) => {
              const fitBand = event.target.value as FitBand;
              onChange(choice.id, { fitBand, manual: true });
              onPersist({ ...choice, fitBand, manual: true });
            }}
            value={choice.fitBand}
          >
            {["Safe", "Moderate", "Ambitious"].map((band) => <option key={band}>{band}</option>)}
          </select>
        </label>
      </div>
      <label className="field-label mt-4">
        Strategy note
        <textarea
          className="field min-h-20 resize-y"
          onChange={(event) => onChange(choice.id, { notes: event.target.value })}
          onBlur={() => onPersist(choice)}
          value={choice.notes}
        />
      </label>
      <div className="mt-3 grid grid-cols-2 gap-2 lg:hidden">
        <button
          className="button-secondary px-3"
          disabled={choice.priority <= 1}
          onClick={() => onJump(choice.id, choice.priority - 1)}
          type="button"
        >
          Move up
        </button>
        <button
          className="button-secondary px-3"
          onClick={() => onJump(choice.id, choice.priority + 1)}
          type="button"
        >
          Move down
        </button>
      </div>
    </article>
  );
}

export default function ChoicesPage() {
  const { user } = useApp();
  const [choices, setChoices] = useState<ChoiceRow[]>(() =>
    choiceDrafts.map((choice) => ({ ...choice, id: `${choice.code}-${choice.branchCode}`, manual: false })),
  );
  const [activeId, setActiveId] = useState(choices[0]?.id ?? "");
  const [snapshot, setSnapshot] = useState("No snapshot saved in this session.");
  const [snapshots, setSnapshots] = useState<SnapshotRecord[]>([]);
  const [pendingImport, setPendingImport] = useState<ChoiceRow[]>([]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [syncStatus, setSyncStatus] = useState("Using preview rows until a workspace choice list loads.");
  const fileRef = useRef<HTMLInputElement>(null);
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const activeChoice = useMemo(() => choices.find((choice) => choice.id === activeId), [activeId, choices]);

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
        setSyncStatus(rows.length ? "Workspace choices loaded from the API." : "Workspace list is empty. Preview rows stay editable.");
      })
      .catch(() => setSyncStatus("API unavailable. Preview mode keeps ordering, notes, and exports usable."));

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
      setSyncStatus(`Saved ${rows.length} priorities to the workspace.`);
    } catch {
      setSyncStatus("Priority order changed locally. API sync is waiting for a reachable workspace.");
    }
  };

  const persistChoice = async (choice: ChoiceRow) => {
    if (!choice.backendId) return;
    try {
      await updateChoice(choice);
      setSyncStatus(`Saved ${choice.code} ${choice.branchCode} metadata.`);
    } catch {
      setSyncStatus("Notes and category changed locally. Metadata sync did not reach the API.");
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
    } catch {
      setSnapshots((current) => [{ title, rows: choices.map((choice) => ({ ...choice })) }, ...current]);
      setSnapshot(`${title} saved locally with ${choices.length} rows and notes at ${new Date().toLocaleTimeString()}.`);
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
    <FeatureGate>
    <div className="space-y-6">
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
        description="Drag rows on desktop, edit one active row at a time on mobile, keep notes visible, and preserve snapshots before filing."
        eyebrow="Primary surface"
        title="Choice filing workspace"
      />
      <input accept=".csv,text/csv" className="hidden" onInput={importCsv} ref={fileRef} type="file" />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <Surface className="space-y-3 p-4 md:p-5" tone="paper">
          <p className="rounded-lg bg-counsly-soft p-3 text-sm text-counsly-body">{syncStatus}</p>
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
          <Surface className="space-y-4 p-5" tone="soft">
            <Badge tone="neutral">Active row</Badge>
            {activeChoice ? (
              <>
                <h2 className="font-display text-3xl text-counsly-ink">{cleanCollegeName(activeChoice.name)}</h2>
                <p className="text-sm leading-6 text-counsly-body">{activeChoice.notes}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="rounded-lg bg-counsly-canvas p-3 text-counsly-muted">Cutoff <strong className="block font-mono text-counsly-ink mt-1 text-lg">{activeChoice.cutoff}</strong></span>
                  <span className="rounded-lg bg-counsly-canvas p-3 text-counsly-muted">Seats <strong className="block font-mono text-counsly-ink mt-1 text-lg">{activeChoice.seats}</strong></span>
                </div>
              </>
            ) : null}
          </Surface>
          <Surface className="space-y-3 p-5" tone="soft">
            <p className="eyebrow">Snapshot status</p>
            <p className="text-sm leading-6 text-counsly-body">{snapshot}</p>
            <div className="space-y-2">
              {snapshots.map((item) => (
                <button
                  className="flex w-full items-center justify-between rounded-lg border border-counsly-line bg-counsly-canvas p-3 text-left text-sm text-counsly-body"
                  key={item.title}
                  onClick={async () => {
                    if (item.id) {
                      try {
                        await restoreChoiceSnapshot(item.id);
                        const rows = await fetchChoices();
                        setChoices(rows);
                        setActiveId(rows[0]?.id ?? "");
                        setSnapshot(`${item.title} restored from the workspace.`);
                        return;
                      } catch {
                        setSnapshot(`${item.title} could not be restored from the API.`);
                      }
                    }
                    if (item.rows) {
                      setChoices(item.rows.map((row) => ({ ...row })));
                      setSnapshot(`${item.title} restored as the local current list.`);
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
                      setSyncStatus(`Imported ${pendingImport.length} rows through the workspace API.`);
                      setPendingImport([]);
                      setPendingFile(null);
                      return;
                    } catch {
                      setSyncStatus("CSV upload did not reach the API. Applying the parsed preview locally.");
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
        <Link className="button-secondary min-w-0 flex-1 px-3" href="/explore">
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
    </FeatureGate>
  );
}
