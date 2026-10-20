# 10 Green fintech audit: Scopus export vs OpenAlex / Crossref rebuild (bibliometrics)

Purpose: compare the database behind Sean's earlier green-fintech manuscript (Scopus export analysed with Bibliometrix and VOSviewer) with a rebuild of the same search on OpenAlex and Crossref; quantify the book-series contamination found in the review (`../track-B-economics-fintech.md`); show how database choice and cleaning change top sources, keywords, thematic map and country ranking.

**Start with `database-comparison.md`.** Paired figures: `figures/C01`-`C07` (sources, keywords, countries, corresponding countries, authors, thematic maps, year distribution); difference tables: `tables/C_difference_table.csv`, `C_difference_summary.csv`, `C_main_information_side_by_side.csv`, `C_thematic_map_clusters_by_corpus.csv`; contamination: `tables/T01_*`; overlap: `tables/T02_*`.

## Corpora
- SR: Scopus export, 168 valid records. SC: cleaned, 155 (13 contaminated by rule, see database-comparison.md section 3). OA: OpenAlex rebuild, 497 records (360 on or before the export date). CR: Crossref comparison set, 191.
- Bibliometrix prefixes in `figures/` and `tables/`: `SR*` raw Scopus, `SC*` cleaned Scopus, `OA*` OpenAlex (`data/clean/M.rds`), `C*` comparison; `P*` Python figures for the OA corpus.
- Date of pull: Scopus file 2026-03-22; OpenAlex/Crossref 2026-10-13 to 2026-10-17.

## Regenerate
```
cd python
python t10_01_scopus_flags.py                     # flags and cleaned Scopus csv
python t10_02_rebuild_openalex_crossref.py        # candidate discovery, OpenAlex/Crossref corpus, overlap tables (cached)
python openalex_search.py 6                       # true OpenAlex search, basic paging (optional, uses anonymous quota)
cd ..\R
Rscript t10_03_scopus_M.R                         # Bibliometrix frames M_scopus_raw.rds / M_scopus_clean.rds (dbsource scopus)
Rscript 01_build_M.R                              # OA frame M.rds
Rscript 02_bibliometrix.R M_scopus_raw.rds SR ID "Scopus export, all 168 records" 2021,2024   # then SC with M_scopus_clean.rds, OA with M.rds
Rscript t10_04_compare.R                          # paired figures and difference table
cd ..\python ; python figures_py.py ; python vosviewer_export.py ; python evidence.py pdfs ; python make_docs.py
```
(`make_docs.py` rewrites `search-protocol.md`; the section 6 counts in the current file were edited by hand afterwards.) The SR and SC runs were made by the earlier agent; the keyword field (default ID = index keywords) and thematic-evolution cut years used for them are not recorded in a log, so the commands above give the script defaults and an assumed 2021,2024 cut. The OA run used ID and cuts 2021,2024 (`data/run_R_OA.log`).

## Limits
- The Scopus search string is reconstructed (the export does not store it); no Scopus or Web of Science login was available, so "Scopus missed it" and "Scopus does not index it" cannot be separated for 243 OpenAlex-only records.
- OpenAlex has no author keywords; keyword comparison mixes Scopus author+index keywords with OpenAlex algorithmic keywords. OpenAlex reference lists are sparse (1,533 references vs 10,672 in Scopus), so co-citation and coupling for OA are weak.
- The OA corpus contains repository records (Zenodo 15) and 137 records dated after the Scopus export.
- Evidence table (`evidence-table.csv`): "method" and "relation" columns are blank because no notes were written for this corpus; "main finding" cells are verbatim abstract sentences. Only 1 of 28 core papers has a legal open PDF reachable (`pdfs/`); the others were closed access, blocked (HTTP 403) or not PDFs. This folder is the database-comparison map only; a separate agent builds the full research pack and its depth layers.
- Earlier code sent a personal e-mail address as a courtesy identifier; removed 2026-10-13.


---
**Repository note:** Files named here under `pdfs/`, `data/raw/scopus/`, `data/raw/s2/`, Scopus-derived CSV/RDS files and `gap-analysis.md` are not part of this repository (see the top-level README, "Not included and why"). Paths in the commands refer to the original working folder.
