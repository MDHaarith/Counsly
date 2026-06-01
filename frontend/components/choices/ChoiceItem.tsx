import { GripVertical } from "lucide-react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Badge } from "@/components/ui";
import { FitBand, toneForBand, cleanCollegeName } from "@/lib/product";

export type ChoiceRow = {
  id: string;
  backendId?: number;
  code: string;
  name: string;
  district?: string;
  type?: "Government" | "Aided" | "Self-Finance";
  branchCode: string;
  branchName: string;
  priority: number;
  fitBand: FitBand;
  notes: string;
  manual: boolean;
  cutoff?: number;
  cutoffRank?: number;
  seats?: number;
  autonomous?: boolean;
  nba?: boolean;
  hostel?: boolean;
  transport?: boolean;
  fees?: number;
  placementRate?: number;
  averagePackage?: number;
  railway?: string;
  distanceKm?: number;
  fitScore?: number;
};

export function ChoiceItem({
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
