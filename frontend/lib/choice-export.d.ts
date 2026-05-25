export type ChoiceExportInput = {
  choices?: Array<{
    branchCode?: string;
    branchName?: string;
    code?: string;
    fitBand?: string;
    name?: string;
    notes?: string;
    priority?: number | string;
  }>;
  exportedAt?: Date;
  student?: {
    chemistry?: number | string | null;
    community?: string;
    maths?: number | string | null;
    name?: string;
    physics?: number | string | null;
  };
};

export type ChoiceExportModel = {
  disclaimer: string;
  exportedAt: string;
  meta: string[];
  rows: string[][];
  title: string;
};

export function buildChoiceExportModel(input?: ChoiceExportInput): ChoiceExportModel;

export function choiceExportFilename(exportedAt?: Date): string;
