# Rebuilds the pack-10 results from raw data, in order. Offline steps run by default; -Network re-runs the API steps (cached, slow).
# Usage: powershell -File rerun.ps1 [-Network]
param([switch]$Network)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path 'D:\')) { throw 'D: is missing - stop.' }
$py   = 'D:\Research-Publishing\_tools\biblio-venv\Scripts\python.exe'
$code = 'D:\Research-Publishing\10-green-fintech-audit\code'
function Run($s) { Write-Host "== $s"; & $py -I -X utf8 (Join-Path $code $s); if ($LASTEXITCODE -ne 0) { throw "$s failed" } }
# 1. Sean's export: flags, repair tables, Table 4 comparison
Run 'screen_export.py'; Run 'repair_tables.py'; Run 'table4_compare.py'
# 2. Rubric scores (quotes are checked against data\fulltext; fails if a quote is missing), second-coder check, wider sample
Run 'rubric_scores.py'; Run 'auto_vs_manual.py'; Run 'wide_sample.py'
# 3. Prevalence analysis from the saved search records, hand-label table, reading notes, appendix
Run 'prevalence_analysis.py'; Run 'hand_label_sample.py'; Run 'build_reading_notes.py'; Run 'build_appendix.py'
if ($Network) {
  # needs internet; every response is cached in data\cache\http.sqlite; S2 and OpenAlex may rate-limit
  Run 'reviews_meta.py'; Run 'abstracts.py'; Run 'refcheck.py'; Run 'verify_unresolved.py'; Run 'test_series_other_dbs.py'
  Run 'prevalence.py'; Run 'build_citations.py'; Run 'network_depth.py'
}
Write-Host 'done'
