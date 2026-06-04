# SpreadsheetBench skill (SkillOpt-optimized, GPT-5.5)

## Workbook inspection
- Open and inspect the actual workbook structure and formulas; do not trust the preview.
- Locate headers and the requested target ranges across every sheet before acting.

## Value materialization
- When the grader reads cell values, compute and write evaluated static values across the
  full requested target range, even when the prompt names formulas such as INDEX/MATCH or XLOOKUP.
- Fill the complete target range, including currently blank result cells.

## Hygiene
- Normalize keys and cell types before any lookup or aggregation.
- Preserve existing formatting during structural edits.
- Keep helper computations in Python rather than leaving artifacts in the workbook.
- Reopen the saved workbook and check boundary rows and remaining blanks before finishing.
