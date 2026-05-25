const FALLBACK_STUDENT = {
  chemistry: null,
  community: "Not set",
  maths: null,
  name: "Counsly student",
  physics: null,
};

/**
 * @typedef {Object} ChoiceExportInput
 * @property {Array<Object>} [choices]
 * @property {Date} [exportedAt]
 * @property {Object} [student]
 */

function numericMark(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function formatAggregate(student) {
  const maths = numericMark(student.maths);
  const physics = numericMark(student.physics);
  const chemistry = numericMark(student.chemistry);
  const aggregate = maths + physics + chemistry;
  return Number.isInteger(aggregate) ? String(aggregate) : aggregate.toFixed(2);
}

function formatDate(date) {
  if (!(date instanceof Date) || Number.isNaN(date.valueOf())) return "Not timestamped";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Kolkata",
  }).format(date);
}

function rowLabel(...parts) {
  return parts.filter(Boolean).join(" ").trim();
}

/**
 * @param {ChoiceExportInput} [input]
 */
export function buildChoiceExportModel(input = {}) {
  const { choices = [], exportedAt = new Date(), student = {} } = input;
  const safeStudent = { ...FALLBACK_STUDENT, ...student };
  const ordered = [...choices].sort((a, b) => numericMark(a.priority) - numericMark(b.priority));

  return {
    disclaimer:
      "This Counsly choice list is advisory planning support, not a guarantee of allotment, admission, fee, seat, or rank outcome.",
    exportedAt: formatDate(exportedAt),
    meta: [
      `Student: ${safeStudent.name || FALLBACK_STUDENT.name} | Community: ${safeStudent.community || "Not set"}`,
      `Cutoff aggregate: ${formatAggregate(safeStudent)} / 200 | Maths ${numericMark(safeStudent.maths)} | Physics ${numericMark(safeStudent.physics)} | Chemistry ${numericMark(safeStudent.chemistry)}`,
      `Generated: ${formatDate(exportedAt)}`,
      `Rows: ${ordered.length}`,
    ],
    rows: ordered.map((choice, index) => [
      String(choice.priority || index + 1),
      rowLabel(choice.code, choice.name),
      rowLabel(choice.branchCode, choice.branchName),
      choice.fitBand || "Not classified",
      choice.notes || "",
    ]),
    title: "Counsly TNEA Choice List",
  };
}

export function choiceExportFilename(exportedAt = new Date()) {
  const stamp = exportedAt instanceof Date && !Number.isNaN(exportedAt.valueOf())
    ? exportedAt.toISOString().slice(0, 10)
    : "draft";
  return `counsly-choice-list-${stamp}.pdf`;
}
