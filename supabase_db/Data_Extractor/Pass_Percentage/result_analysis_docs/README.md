# HSE(+2) Result Analysis Sources

This folder tracks Tamil Nadu HSE(+2) result-analysis / pass-percentage sources for 2020-2025 so the prediction notebook can include board-result difficulty context.

## Files

- `hse_plus2_result_analysis_2020_2025_summary.csv` - compact year-level features used by the Colab notebook.
- `pdfs/` - locally saved PDFs where a direct public PDF download was available.

## Source Coverage

- 2024 and 2025 are official DGE/TNEGADGE S3 PDFs.
- 2020 and 2023 are third-party pages linking public Google Drive PDFs.
- 2022 is captured from a Kalviexpress summary page; its Box PDF did not download directly in this environment.
- 2021 is a COVID special evaluation year, so it is kept as summary-only with `100.00` pass percentage and no normal exam-analysis PDF.

Use `source_class` in the CSV to separate official PDFs from third-party summaries when training or auditing.
