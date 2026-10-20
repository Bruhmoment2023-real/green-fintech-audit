# The 15 green-fintech reviews: what I could open, what each reports

List and DOIs: Track B section 2.4 (every DOI re-resolved in Crossref on 17 Oct 2026, `data/reviews15_meta.csv`). "Opened in full" = I extracted and read the PDF text (and viewed flow-diagram images). "Abstract only" = abstract retrieved from OpenAlex or Semantic Scholar, full text not reachable. "Metadata only" = Crossref record, no abstract.

## Access result (honest count)
- **Opened in full: 5 of 15** (#1, #4, #6, #9, #10). Scored with the full rubric.
- **Abstract only: 9** (#2, #3, #5, #8, #11, #12, #13, #14, #15). Coded for the four things an abstract can show (database, number of records, period, software).
- **Metadata only: 1** (#7, SSRN preprint; the SSRN page returned an HTTP 403 and OpenAlex has no abstract).
- Of the 10 without full text, an open-access copy exists for 6 but my automated fetch was blocked (HTTP 403 or a Cloudflare challenge); I did not try to get round the block: #3 (university repository, green OA), #5, #8, #12, #15 (Elsevier, open licence), #7 (SSRN). Four are paywalled (#2 Emerald, #11 Emerald, #13 Wiley, #14 Wiley). Links for Sean to open by hand in a browser are in `results/MANUAL-DOWNLOAD-LIST.md`.
- #1 (Kwong) is also Sean's own PDF on E: (byte-identical to the copy I fetched from a repository). #4 and #10 were fetched from MDPI's article CDN (`mdpi-res.com`) because www.mdpi.com returned 403 to my client; #6 from the journal's own site; #9 from EconStor. If Sean prefers that the CDN route not be used, these two PDFs can be deleted from `E:\Research-Staging\10-green-fintech-audit\pdfs\`.

## Table (database, size, period as the authors state them)

| # | Review | Outlet, year | Access | Database(s) | Records analysed | Period | Software stated | Rubric % (full text only) |
|---|---|---|---|---|---|---|---|---|
| 1 | Kwong, Kwok, Wong | Sustainability 2023 | full | Web of Science Core Collection (SSCI, SCIE, ESCI, AHCI) | 776 fintech + 1,428 green finance/ESG sets | to 2022 | Bibliometrix (no version), VOSviewer 1.6.18 | 60.0 (core 50.0) |
| 2 | Dar, Badwan, Kumar | IJIMEFM 2024 | abstract | Scopus and Dimensions | 665 | 2015-2023 | "similarity viewer" (VOSviewer implied); Biblioshiny named as an alternative | - |
| 3 | Lucarelli, Mazzocchini, Severini | Int J Green Economics 2024 | abstract | "two robust repositories" (not named in abstract) | 75 | not in abstract | SPAR-4-SLR protocol named | - |
| 4 | Saeedi, Ashraf | JRFM 2024 | full | Scopus and Google Scholar | about 800 screened, 90 included | 2013-2024 | none (narrative survey) | 43.8 (R8, R9 not applicable) |
| 5 | Kozar, Wodnicka | Procedia CS 2024 | abstract | Scopus | 52 | 2019-2023 | VOSviewer | - |
| 6 | Sethi, Mahadik | Cent Eur Bus Rev 2024 | full | Scopus | 215 retrieved, 116 final | 2017-2023 | Biblioshiny, VOSviewer, WordStat (no versions) | 65.0 (core 57.1) |
| 7 | Aggarwal, Joshi, Gupta, Kaushik | SSRN 2024 | metadata | unknown | unknown | unknown | unknown | - |
| 8 | Bansal et al. | RIBAF 2025 | abstract | Web of Science | 168 | not in abstract | not in abstract | - |
| 9 | Zournatzidou | Admin Sci 2025 | full | Scopus | 945 identified, 299 included | 2019-2025 | R "3.6.0+", Biblioshiny, VOSviewer | 55.0 (core 57.1) |
| 10 | Fotova Cikovic, Cvetkoska, Primorac | JRFM 2025 | full | Web of Science Core Collection (ESCI, SCIE, SSCI) | 1,261 identified, 268 included | all years; search June 2025 | Bibliometrix 5.1.0, VOSviewer 1.6.20 | 80.0 (core 78.6) |
| 11 | Magableh et al. | JSTPM 2025 | abstract | Web of Science and Scopus | not in abstract | not in abstract | VOSviewer | - |
| 12 | Kozar, Warwas | Procedia CS 2025 | abstract | Scopus | not in abstract (18 research areas) | not in abstract | VOSviewer | - |
| 13 | Jaiswal, Satyanisth | Sustainable Dev 2025 | abstract | Scopus | 472 | 2017-2025 | not in abstract | - |
| 14 | Hassan, Zahra, Farouk, Hussin | Bus Strategy Dev 2026 | abstract | Scopus | 228 | 2020-2025 | VOSviewer, R Studio (Bibliometrix) | - |
| 15 | Karim, Roshid, Dhar, Waaje | Sustainable Futures 2026 | abstract | Scopus | 72 | 2019-2024 | not in abstract | - |
| S0 | Sean's manuscript, 24 May 2026 (self-audit, not one of the 15) | unpublished | full | Scopus | 1,200 retrieved, 168 final (155 after removing 13 off-topic) | to March 2026 | VOSviewer 1.6.18, Bibliometrix (no version) | 40.0 (core 42.9) |

Abstract-level reporting among the 9 reviews with an abstract: database named in 8 (the exception is #3), number of records in 7, period in 5, software named explicitly in 4 (5 counting #2's "similarity viewer"). Dates of search, search strings, counts per stage, cleaning and data sharing cannot be seen from an abstract and are not counted.

## What the five full-text scores show (score file: `rubric_scores_long.csv`, evidence for each cell)
- Items reported by all five: database named (R1 = 2 in all five).
- Items weakest across the five: search date (R3: one review gives a month and year, two give nothing, two give an indirect date), cleaning (R7: nobody scores 2; none describe a de-duplication method or software), and data (R10: nobody deposits records; three give a statement ("on request" twice, "restrictions apply" once) and two give none).
- Search string (R2): none of the five reports a string that could be pasted into the database as it stands; Sethi 2024 comes closest (two terms, AND, title-abstract-keyword). Zournatzidou 2025 prints ten alternative strings and does not say which one returned the 945 records.
- Internal inconsistencies found while reading (not scored):
  - Fotova Cikovic et al. 2025: the text says the 1,261 records were narrowed to 268 by the Web of Science category "Business Economics"; Figure 2 reaches 268 through 485 duplicates, 131 screened out, 282 not retrieved and 95 non-English exclusions. Arithmetic in the figure checks out (1261-485=776; 776-131=645; 645-282=363; 363-95=268). 485 duplicates from one database also needs explaining.
  - Sethi and Mahadik 2024: the text says reviews, proceedings and book chapters were excluded; Figure 2 lists "Article" as the document type and several subject areas the text never mentions.
  - Zournatzidou 2025: the PRISMA arithmetic checks out (945-80-82=783; 783-124-147=512; 512-213=299), but "R 3.6.0+" and "RStudio version 3.6.0 or above" conflate R and RStudio version numbers, and the text says the search criteria "were modified" without giving the modified string.
  - Kwong et al. 2023: calls the work a bibliometric analysis, uses Web of Science and the keyword set for green finance includes ESG; its own data statement says restrictions apply to the data. (Sean's manuscript copies the template but uses Scopus.)
- Scale: reviews of what is nominally the same field analyse between 52 and 1,428 records, because they define the field differently (fintech-and-green-finance only, versus sustainability, versus ESG, versus AI). Nobody can compare their rankings without re-running them, which is the point of the audit; the Phase 2 OpenAlex/Scopus comparison (`../bibliometrics/database-comparison.md`) shows how far top-ten lists move from the database alone (Jaccard 0.33 for sources between cleaned Scopus and OpenAlex).

## Not done (needs access)
- Full-text scoring of 10 of the 15 reviews. With the six open copies downloaded by hand (list in `MANUAL-DOWNLOAD-LIST.md`), `code/rubric_scores.py` needs only new rows (quote + score) added to its dictionary; it will refuse any quote that is not in the text.
- A second human coder.
