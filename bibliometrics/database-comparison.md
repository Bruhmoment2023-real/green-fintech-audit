# Database comparison: Scopus export vs OpenAlex (and Crossref) rebuild, and the effect of cleaning

Data only, no manuscript prose. Every number is in a CSV under `tables/` (names in brackets). Scripts: `python/t10_01_scopus_flags.py`, `python/t10_02_rebuild_openalex_crossref.py`, `python/openalex_search.py`, `R/02_bibliometrix.R` (run three times with prefixes SR, SC, OA), `R/t10_04_compare.R`.

## 1. The three corpora
| Label | Source | Records | Notes |
|---|---|---|---|
| SR | Sean's Scopus export, `fntech green finance.csv` (file dated 2026-03-22; read-only copy in `data/raw/scopus/`), loaded with Bibliometrix `dbsource = "scopus"` | 168 valid (169 rows; 1 malformed row, a reference fragment split across columns, dropped) | Search string is not stored in the export; reconstructed as `TITLE-ABS-KEY(fintech AND "green finance")`, 2021-2026, articles and reviews. All 168 records satisfy it. |
| SC | SR minus contaminated records | 155 | Rule in section 3. |
| OA | OpenAlex rebuild of the same string | 497 (360 dated on or before the Scopus export date) | English articles and reviews 2021-2026, title-and-abstract match for `fintech AND "green finance"`, title de-duplicated. Built from two routes merged (section 2). |
| CR | Crossref | 191 journal articles with the string in Crossref's own title+abstract | Used for overlap only; not analysed in Bibliometrix (Crossref has no keywords or affiliations of the kind needed). |

Pull dates: OpenAlex and Crossref 2026-10-13 to 2026-10-17; Scopus export 2026-03-22. The OA corpus therefore contains 137 records published after the export date (`T02_openalex_only_records.csv`, column `after_scopus_export_date`).

## 2. How OpenAlex was rebuilt, and what the two routes show
- Route 1 (emulated): candidate DOIs from Semantic Scholar Boolean search, Crossref free-text search and the Scopus export itself, then each DOI looked up in OpenAlex and the same string applied to OpenAlex's own title and abstract. Used first because the keyless OpenAlex search quota was spent on 2026-10-13.
- Route 2 (true OpenAlex search, run after the quota reset): `title_and_abstract.search:fintech AND "green finance"` with `publication_year:2021-2026,type:article|review`: 574 hits, all pages fetched by basic paging (cursor paging now needs a key) [`T02_openalex_search_validation.csv`].
- Of the 574 true hits, 519 also satisfy the local string rule; 449 had already been found by route 1. 119 string-matching works were found only by the true search and 92 only by route 1. The final OA corpus is the union after the language, type and title de-duplication filters, which is why neither route alone is used.

## 3. Contamination: rule and count [`T01_scopus_record_flags.csv`, `T01_contamination_summary.csv`]
Rule (three flags per record, all visible in the table):
- R0 keyword-only match: fintech and "green finance" are not both in title + abstract (35 of 168).
- R1 inherited keyword block: the record belongs to a source with at least 3 records in the export whose author-keyword lists all contain the same block of at least 4 keywords including both search terms (15 records, all in `Review of Management Literature`, block: AI finance; Digital leadership; Fintech; Green finance; Supply chain resilience; Sustainable finance).
- R2 no topic term: no fintech, financial-technology, digital-finance, green-finance/bank/bond/credit/investment, sustainable-finance or climate-finance term in title + abstract (14 of 168).
- CONTAMINATED = R1 and R2: **13 of 168 (7.74 percent)**, matching the earlier review's count. Two records in the same block are on topic and kept (`Adoption of Green Banking and Finance...`, `Artificial Intelligence in Sustainable Finance...`). One record outside the block fails R2 and is listed for hand check, not removed (`Funding sustainable shipping: ...`, a transport journal).
- The 13 include a front-matter record titled `Prelims`, the series volume record, and workplace/HR reviews (workplace deviance, employee engagement, happiness at work, and similar).
- Effect of cleaning on headline counts: author keyword "fintech" 107 to 94; "sustainable finance" 23 to 10; "ai finance", "digital leadership", "supply chain resilience" 15 to 2 each; reviews 29 to 18; the series editor as author 15 to 2; `Review of Management Literature` rank 2 (15 records) to rank 17 (2 records). Cleaning changes the corpus by 7.7 percent of records but the keyword and source tables by far more at specific places.
- None of the 13 contaminated records is in the OA corpus (0 of 13), because OpenAlex matched on title and abstract rather than on volume-level keywords.

## 4. Record-by-record overlap by DOI [`T02_overlap_summary.csv`, `T02_scopus_records_in_other_databases.csv`, `T02_openalex_only_records.csv`]
- Scopus 168: 166 have an OpenAlex record by DOI; 113 have an abstract in OpenAlex; **105 are in the OA corpus**. Of the 155 cleaned, 105 are in OA. Jaccard overlap (SC vs OA, by DOI) = 0.207.
- Scopus-only (not in OA corpus, 63): 31 because the search terms are only in Scopus keywords (index keywords) and not in OpenAlex title or abstract; 30 because OpenAlex holds no abstract and the title lacks the terms; 2 with no OpenAlex record for the DOI.
- OpenAlex-only (392 records not in the Scopus export): 243 journal records dated before the export whose source is not in Scopus or that the Scopus search missed (cannot be told apart without Scopus access); 137 published after the export date; 10 preprint or repository records (Scopus does not index them); 2 with no source recorded.
- Crossref: 166 of the 168 Scopus records exist in Crossref; only 82 carry an abstract there, and 89 are findable by the string in Crossref's own title+abstract. Crossref is therefore a weak search substitute here.

## 5. Distributions
- Year [`SR02/SC02/OA02_annual_production.csv`, figure `C07_paired_year_distribution`]: Scopus 2021 to 2026 = 3, 3, 18, 53, 75, 16 (cleaned: 2025 = 62); OA = 9, 10, 27, 74, 182, 195. OA is larger in every year and larger after the export date by construction; the latest points of both are part-year.
- Source [`C_difference_table.csv`, figure `C01`]: top Scopus sources are Resources Policy (31), Review of Management Literature (15, contaminated), Sustainability (14), Sustainable Development (10). OA top sources are Zenodo (15, repository records typed as article), Resources Policy (14), Sustainability (14), Sustainable Development (12). 77 distinct sources in Scopus versus 338 in OA.
- Document types: Scopus 138 articles and 29 reviews (18 after cleaning); OA 470 articles and 27 reviews.
- Citations: average citations per document 22.42 (SR), 24.29 (SC), 14.08 (OA); OA is younger (average age 1.0 versus 1.6 years).
- References: 10,672 (SR) and 9,687 (SC) cited references versus 1,533 in OA; OpenAlex reference lists give far less for co-citation analysis here.

## 6. Standard outputs side by side [`C_difference_summary.csv`, `C_difference_table.csv`, figures `C01`-`C06`]
Overlap of the top-N lists (Jaccard) and Spearman rank correlation on items present in both:

| Output | Top N | Cleaning effect (SR vs SC) | Database effect (SC vs OA) |
|---|---|---|---|
| Sources | 10 | 9 shared, Jaccard 0.82, same number one (Resources Policy), rho 0.996 | 5 shared, Jaccard 0.33, number one differs (Zenodo in OA), rho 0.82 |
| Keywords | 15 | 11 shared, 0.58, same number one, rho 0.990 | 8 shared, 0.36, rho 0.51 (different fields: Scopus author keywords vs OpenAlex algorithmic keywords) |
| Countries (all authors) | 10 | 8 shared, 0.67, same number one (China), rho 0.997 | 6 shared, 0.43, same number one, rho 0.85 |
| Corresponding-author countries | 10 | 10 shared, 1.00, rho 1.00 | 8 shared, 0.67, rho 0.69 |
| Authors | 10 | 9 shared, 0.82, rho 1.00 | 2 shared, 0.11, rho 0.62 |

Specific moves worth checking in the table:
- Cleaning: `Review of Management Literature` falls from rank 2 to 8 then out of the top 10 (n 15 to 2); "sustainable finance" falls from rank 3 to 8 (23 to 10); the three block keywords drop from rank 7 (15 each) to rank 45 (2 each); India falls from rank 2 to 4 (27 to 19) and the UAE from rank 5 to 9 (19 to 6) (the n columns show the drop; the table does not say why, and I did not trace the affiliations of the 13).
- Database: "natural resources" is rank 3 in cleaned Scopus (18) and rank 194 in OA (4); "blockchain" rank 24 in Scopus and 4 in OA; "green bonds" rank 45 and 9; "financial inclusion" rank 7 and 3. China is rank 1 in both. Indonesia (50), Pakistan (56) and India (69) rise in OA.
- Thematic map [`C_thematic_map_clusters_by_corpus.csv`, figure `C06`]: Scopus raw has a "sustainable finance" cluster built from the contaminated block (digital leadership, supply chain resilience, AI finance); cleaned Scopus has fintech, green finance, sustainable development, sustainability, financial inclusion and economic growth clusters; OA has green finance, financial inclusion (with blockchain), fintech adoption, green bonds and digital payments. In cleaned Scopus "natural resources" and "environmental sustainability" sit inside the fintech cluster; they are small in OA (natural resources n = 4).
- Main information [`C_main_information_side_by_side.csv`]: international co-authorship 46.4 percent (SR), 43.9 percent (SC), 22.3 percent (OA); co-authors per document 3.10, 3.15, 2.74. OA has no author keywords at all (field DE = 0), so keyword analysis uses OpenAlex keywords for OA and author plus index keywords for Scopus.

## 7. Cautions
- The Scopus search string is reconstructed, not recorded; the Scopus export is a March 2026 snapshot and OA is an October 2026 pull, so 137 OA-only records are a date effect, not a database effect. Section 4 separates them.
- "OpenAlex-only, before export date" (243) cannot be split into "Scopus does not index this source" and "Scopus search missed it" without Scopus access. A Scopus re-run of the string in `scopus-queries.md` would settle it.
- OA includes Zenodo and other repository records typed "article" (15 Zenodo records, plus 6 with no source); no filter on source type was applied beyond OpenAlex's type field.
- Rankings with small counts (n of 2 to 4) change with single records; read rank changes together with the n columns.
- OpenAlex keywords are algorithmic and not comparable with author keywords; countries come from different affiliation parsing; the OA 497 are not a sample of the Scopus 168 but an independent search.
