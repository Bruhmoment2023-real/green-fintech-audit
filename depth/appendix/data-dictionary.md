# Data dictionary (pack 10)

Generated 2026-10-17 by `code/build_appendix.py`; counts read from the files. "Known problems" lists what I know is wrong or limited.

| Path | Source and date | Rows | Columns | Meaning of variables and known problems |
|---|---|---|---|---|
| data/source/scopus_export_original.csv | Sean's Scopus export, byte copy of E:\Downloads Copy\fntech green finance.csv (file dated 2026-03-22) | 169 | Authors; Author full names; Author(s) ID; Title; Year; Source title; Volume; Issue; Art. No.; Page start; Page end; Cited by; DOI; Link ... (75) | Scopus CSV columns (75, many empty); one record is split over two rows by a line break inside a References field; Year column of the broken row holds page text. |
| data/source/manuscript_2026-05-24.docx | Copy of "Fintech Manuscrip Final (1).docx" (saved 24 May 2026) |  |  | Binary; text extracted on the fly. |
| data/scopus_export_flags.csv | Export with my flags (row = spreadsheet row, has_fin_ta, has_grn_ta, has_ft_ta, has_gf_ta, series, lexical_core) | 168 | Authors; Author full names; Author(s) ID; Title; Year; Source title; Volume; Issue; Art. No.; Page start; Page end; Cited by; DOI; Link ... (82) | Flags are lexical tests on title+abstract; lexical_core False for 15 records (14 series, 1 shipping). |
| data/reviews15_meta.csv | Crossref and OpenAlex metadata for the 15 reviews, retrieved 2026-10-17 | 15 | n; label; doi; cr_status; title; container; cr_type; year; authors; license; oa_status; oa_url; best_pdf; best_land ... (18) | oa_status, oa_url, best_pdf from OpenAlex; n_refs_crossref is the reference count Crossref holds. |
| data/reviews15_abstracts.json | Abstracts of the 15 reviews from OpenAlex (inverted index rebuilt) and Semantic Scholar where available | 15 | dict of items | Empty string = no abstract found. |
| data/prevalence/search_records.csv | Rows returned by 50 topic queries on Crossref (top 100 each) and Semantic Scholar (first 7 queries), 2026-10-17 | 5700 | src; q; id; title; year; venue; rtype; has_abstract; query_terms_in_own_title_abstract; terms_only_via_container; front_matter (11) | src; q; id (DOI); title; year; venue (container/venue); rtype (journal, proceedings, book/series, other:*); has_abstract; query_terms_in_own_title_abstract; terms_only_via_container (Crossref); front_matter. |
| results/rubric_scores_long.csv | One row per paper x rubric item with score, verbatim evidence quote, PDF page and note | 60 | paper; item; item_name; score; evidence_quote; pdf_page; note (7) | score 0/1/2 or empty for not applicable; quotes machine-checked. |
| results/rubric_scores_wide.csv | Scores by paper (R1-R10), total, maximum, percent, core percent | 6 | paper; R1; R2; R3; R4; R5; R6; R7; R8; R9; R10; total_scored; max_applicable; pct ... (15) | NA = not applicable. |
| results/auto_vs_manual.csv | Regex detector versus manual "reported at all" per paper and item | 53 | paper; item; auto_detected; manual_reported; agree (5) | agree = detector and manual coincide. |
| results/wide_sample_abstract_coding.csv | Regex coding of abstracts of 98 review-type records from the Phase-2 corpus | 98 | id; title; year; venue; doi; primary_sublit; is_bibliometric; A1_database; A2_n_records; A3_period; A4_software; A5_protocol (12) | A1 database, A2 number of records, A3 period, A4 software, A5 protocol; is_bibliometric. |
| results/series_other_databases.csv | Crossref and OpenAlex metadata for the 15 series records | 15 | title; doi; scopus_author_keywords; scopus_has_abstract; crossref_status; crossref_type; crossref_container; crossref_subject; crossref_has_abstract; openalex_status; openalex_type; openalex_source; openalex_source_type; openalex_keywords ... (18) | openalex_keywords are OpenAlex's own; flags test for the volume keyword block. |
| results/prevalence_hand_labelled_sample.csv | 60 random Crossref book/proceedings records (container-only matches) with my hand label | 60 | q; id; title; venue; rtype; hand_label (6) | F front/back matter, G generic or unrelated, B borderline, R relevant. |
| results/repair/screening_decisions.csv | Include/exclude/borderline decision for each of the 168 export records with reason | 168 | row; Authors; Title; Year; Source title; Document Type; Cited by; DOI; decision; reason (10) |  |
| results/repair/table2_keywords.csv | Keyword counts raw and clean | 25 | keyword; raw_168; clean_155 (3) |  |
| results/repair/table3_countries.csv | Records per country raw and clean (one count per record) | 20 | country; records_raw; records_clean (3) |  |
| results/repair/table4_comparison.csv | Manuscript Table 4 rows against the export (title similarity, source ok, citations ok) | 10 | rank; ms_title; export_title; title_similarity; title_exact; ms_year; export_year; year_ok; ms_source; export_source; source_ok; ms_cites; export_cites; cites_ok ... (15) |  |
| results/repair/table4_corrected_top12.csv | Corrected top-cited list from the cleaned export | 12 | Title; Year; Source title; cit; DOI; Authors (6) |  |
| results/repair/reference_check_crossref.csv | Best Crossref match for each of the 19 manuscript references | 19 | ref; cited; cited_year; best_title; best_doi; best_year; best_container; best_vol; best_issue; best_page; best_first_author; title_similarity (12) | title_similarity is difflib ratio. |
| results/repair/reference_verdicts.csv | Hand verdict per reference (resolves, does not resolve, mis-cited, unconfirmed) | 19 | ref; cited_as; verdict; note; crossref_best_doi (5) |  |
| results/repair/intext_vs_list.csv | In-text author-year citations versus the reference list (regex; checked by hand) | 11 | first_author; year; in_reference_list (3) | The regex misses some citation forms; the final list is in the repair appendix. |
| depth/network/keyword_bursts.csv | Kleinberg bursts per OpenAlex keyword | 12 | keyword; total; burst_start; burst_end; weight; counts_by_year (6) | weight = summed cost difference over the burst years. |
| depth/network/main_path_papers.csv | Papers on the global main path in citation order | 10 | order; id; year; first_author; title; venue; doi; on_keyroute (8) | on_keyroute flag. |
| depth/network/key_route_papers.csv | Papers on key routes | 18 | id; year; title; doi (4) |  |
| depth/network/data/snapshot_master.csv | Copy of the Phase-2 corpus (497 OpenAlex records) taken on the run date | 497 | id; title; abstract; year; pub_date; venue; doc_type; authors; author_ids; n_authors; doi; arxiv_id; acl_id; dblp_key ... (49) | See bibliometrics/ for its own documentation. |
| depth/network/data/snapshot_references.csv | Copy of Phase-2 reference links (citing, cited OpenAlex ids) | 12932 | citing; cited; cited_title; cited_year; cited_first_author; cited_venue; cited_doi; cited_arxiv; cited_acl; in_corpus; cr (11) |  |
| depth/citations/references.bib | BibTeX from Crossref | 47 | - |  |

## Text copies (data/fulltext/*.txt)
Extracted text (pypdf or Europe PMC XML) of the PDFs and articles I opened: review01/04/06/09/10, guideline_biblio/prismas/prisma2020, donthu2021, baas2020, gusenbauer2019/2020, zupic2015, ellegaard2015, arxiv2508_16276, koo2023_priba. Source PDFs are in E:\Research-Staging\10-green-fintech-audit\pdfs\ (see STAGING.md). Known problems: pypdf drops some figure text and splits words at line breaks; quotations are checked with whitespace, hyphenation and ligature normalisation. Copyright: texts are for local analysis only and are not redistributed.

## HTTP cache
data/cache/http.sqlite holds every API response (200 and 404 only) so re-runs are deterministic for the dates shown; it is a cache, not a deliverable.


---
**Repository note:** files under `data/source/`, `data/fulltext/`, `data/cache/`, `data/scopus_export_flags.csv` and `data/reviews15_abstracts.json` listed above are not included in this repository. `results/repair/screening_decisions.csv` was reduced to row, year, document type, DOI, decision and reason; the two record-level Scopus tables in `bibliometrics/tables/` were reduced similarly.
