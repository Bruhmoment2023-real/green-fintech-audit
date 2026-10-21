# Can green-fintech bibliometric reviews be re-run? A reporting audit and a test of metadata contamination

Archived on Zenodo: https://doi.org/10.5281/zenodo.23537670 (this DOI always points to the latest version).

**Author:** Sean Solano Paul, Independent researcher, Bengaluru, India.
**Funding:** none. **Competing interests:** none.

## Summary

A bibliometric review can be repeated only if it reports how its records were found and cleaned. This repository holds the code, derived data and results behind a reporting audit of 15 green-finance and fintech reviews published 2023 to 2026. A ten-item checklist was built from published guidelines (BIBLIO, PRIBA, PRISMA-S, PRISMA 2020) and applied to the five reviews readable in full and to the author's own earlier manuscript. A prevalence test over 50 Crossref queries (plus 7 Semantic Scholar queries) measures how often book-series, proceedings and front-matter metadata leaks into topic searches. The author's own 168-record Scopus corpus was then repaired (13 records removed as series contamination), and a parallel corpus was rebuilt from OpenAlex and Crossref (497 records) to show how database choice and cleaning change the top-ten tables.

## Repository layout

| Path | Contents |
|---|---|
| `docs/design.md` | Pre-specified research questions, hypotheses, data sources and analysis plan |
| `code/` | Audit scripts (rubric scoring, auto-vs-manual coding, wide-sample coding, prevalence test, repair tables, reference checks, network analysis); `code/README.md` |
| `results/` | Rubric (`RUBRIC.md`), rubric scores, prevalence and wide-sample results, repair tables (`results/repair/`), summaries |
| `repair-appendix/` | Written appendix on the repair of the earlier manuscript's data |
| `data/` | Derived data and logs: review metadata, prevalence search records, small logs |
| `bibliometrics/` | Database-comparison pipeline: `python/`, `R/`, `config.json`, `tables/`, `figures/`, `vosviewer/` files, `data/clean/` (OpenAlex and Crossref corpus), `data/raw/` (OpenAlex and Crossref API responses), protocol documents. Figure and table prefixes: `SR*` raw Scopus, `SC*` cleaned Scopus, `OA*` OpenAlex, `C*` comparison, `P*` Python figures. See `bibliometrics/README.md` and `bibliometrics/database-comparison.md` |
| `depth/` | BibTeX/RIS reference lists, keyword-burst and main-path network analysis, data dictionary and `rerun.ps1` |

## How to reproduce

- Python 3.12; install with `pip install -r requirements.txt`. R 4.5.3 with `bibliometrix` 5.3.0, `igraph` 2.2.2, `ggplot2` 4.0.3, `dplyr` 1.2.0, plus `data.table`, `ggrepel`, `jsonlite`, `Matrix`, `stringr`, `tidyr` (needed only for the bibliometrix figures and tables).
- Run order for the audit scripts is in `depth/appendix/rerun.ps1` (offline steps first; `-Network` re-runs the API steps). Order: `screen_export.py`, `repair_tables.py`, `table4_compare.py`, `rubric_scores.py`, `auto_vs_manual.py`, `wide_sample.py`, `prevalence_analysis.py`, `hand_label_sample.py`, `build_reading_notes.py`, `build_appendix.py`; network steps: `reviews_meta.py`, `abstracts.py`, `refcheck.py`, `verify_unresolved.py`, `test_series_other_dbs.py`, `prevalence.py`, `build_citations.py`, `network_depth.py`.
- The bibliometrix comparison is described step by step in `bibliometrics/README.md` ("Regenerate").
- Scripts were written with absolute paths under the original working folder (`D:\Research-Publishing\10-green-fintech-audit`); edit the path constants at the top of each script (and in `code/netcache.py` and `bibliometrics/python/bm_common.py`) to match your checkout. Network steps cache responses locally; API responses can change over time, so a fresh pull will not match the pinned snapshots exactly.
- Steps that need files listed under "Not included" (the Scopus export, publisher full texts for the rubric quotation check) require you to obtain those files first.

## Data sources and licences

| Source | Use | Licence / terms |
|---|---|---|
| OpenAlex API (works, references, search) | Corpus of 497 records; raw responses in `bibliometrics/data/raw/openalex*` | CC0 |
| Crossref REST API | Comparison corpus (191 records), DOI lookups, prevalence test, reference checks | Factual metadata, openly available (Crossref terms of use) |
| Semantic Scholar Graph API | 7 prevalence queries; only summary columns in `data/prevalence/search_records.csv` | Semantic Scholar API licence; raw responses not redistributed |
| Scopus export (March 2026, 168 records) | Starting corpus for the repair | Elsevier Scopus terms; raw export not redistributed. Record-level files here are reduced to identifiers, years, types and derived flags |
| Reporting guidelines (BIBLIO, PRIBA, PRISMA-S, PRISMA 2020) and the 15 reviews | Rubric items scored from the text | Original publisher terms; only short checked quotations appear in `results/rubric_scores_long.csv` |
| Author-derived tables, figures, documents | Everything else | CC BY 4.0 (`LICENSE-DATA.md`) |

Third-party author e-mail addresses that appeared in retrieved API records were replaced with `[email removed]` in the included data.

## Not included and why

- Abstract text: the `abstract` columns of the bibliographic tables, the verbatim-from-abstract column of `bibliometrics/evidence-table.csv`, and the raw OpenAlex API dumps (`bibliometrics/data/raw/openalex/`). Regenerate with the bibliometrics pipeline (OpenAlex is free).
- Per-paper reading notes on the literature (they contain quotations from copyrighted papers) and the literature gap-analysis note (scoping). The scripts that built the notes are kept; run them on your own copies of the papers.
- Scopus export and files that reproduce it record by record (`data/source/scopus_export_original.csv`, the flagged copy, `bibliometrics/data/raw/scopus/`, cleaned Scopus CSVs, `M_scopus_*.rds`): vendor data under Scopus terms. Obtain a Scopus export with the search string in `bibliometrics/scopus-queries.md` and `bibliometrics/search-protocol.md`. In `bibliometrics/tables/` the two record-level Scopus tables (`T01_scopus_record_flags.csv`, `T02_scopus_records_in_other_databases.csv`) and `results/repair/screening_decisions.csv` were reduced to identifiers, year, type, flags and decisions (titles, authors, source titles and keywords removed).
- Publisher full-text PDFs and their text extractions (`data/fulltext/`, `data/pages/`, `staged-from-E/`, `bibliometrics/pdfs/`): copyrighted. Re-fetch open-access copies with `code/fetch_method_papers.py`, `code/dl*.py` and the PDF step in `bibliometrics/python/`.
- The earlier manuscript (`data/source/manuscript_2026-05-24.docx`): unpublished draft that is the object of the repair; the repair is documented in `repair-appendix/`.
- Semantic Scholar raw responses (`bibliometrics/data/raw/s2/`) and `data/reviews15_abstracts.json` (abstract text of the reviews): third-party text; regenerate with `code/abstracts.py` and `bibliometrics/python/pipeline.py`.
- HTTP cache (`data/cache/http.sqlite`), scratch copies and working notes (prior-work memo, gap analysis): regenerated by the scripts or not needed.
- Nothing exceeded 50 MB. The largest included file is `bibliometrics/data/raw/openalex/works.jsonl` (about 35 MB).

## Notes and limits

- Only 5 of the 15 reviews could be read in full; the checklist scores cover those five plus the author's own manuscript.
- The Scopus search string is reconstructed (the export does not store it).
- The bibliometrix keyword field and thematic-evolution cut years for the `SR*` and `SC*` runs were not logged; `bibliometrics/README.md` gives the assumed values.

## Citation

Solano Paul, S. (2026). *Can green-fintech bibliometric reviews be re-run? A reporting audit and a test of metadata contamination* [Software and data]. Independent researcher. See `CITATION.cff`. A DOI will be added when the repository is archived.
