# Appendix A: repair of the data in "Green Finance and FinTech: A Bibliometric and Network Analysis" (file saved 24 May 2026)

Source files (read only, copied to `data/source/`): `fntech green finance.csv` (Scopus export, md5 4526b6b3..., byte-identical to `fntech green finance (1).csv`) and the manuscript docx. Every number below was recomputed from the export by `code/screen_export.py`, `code/repair_tables.py`, `code/table4_compare.py`, `code/refcheck.py`, `code/verify_unresolved.py`; tables are in `results/repair/`. This appendix is data, not manuscript text.

The export has 169 rows; one (row 88, "Rana S.; Islam M.Z.") is split across two rows by a line break inside a References field, leaving 168 valid records. The 168 valid rows parse as 138 articles, 29 reviews and one record whose document type sits in the broken fragment; the fragment's document-type field reads "Review", and the manuscript's document-type table ("Article 138, Review 30") counts that record as a review (checked against the export and the manuscript, 21 October 2026).

## A1. Contaminated records (`results/repair/screening_decisions.csv`)
- 15 of 168 records (8.9 percent) have the source "Review of Management Literature", an Emerald book series volume. All 15 carry the identical keyword block "AI finance; Digital leadership; Fintech; Green finance; Supply chain resilience; Sustainable finance" and the series editor (Rana S.) as first author.
- Decision by reading title and abstract: **13 excluded (7.7 percent of 168)**: one record titled "Prelims", one titled "Review of Management Literature" (the volume record), and eleven chapters on workplace deviance, employee engagement, happiness at work, performance orientation, retirement planning, sustainable HRM, digital leadership, supply chain resilience and AI, multi-agent manufacturing, organisational behaviour and indigenous data sovereignty. **Two chapters kept** (green banking and finance; AI in sustainable finance) because they are on topic.
- One further record is flagged, not removed: "Funding sustainable shipping: a fuzzy cognitive mapping approach to the Poseidon Principles" (Transportation Research Part D): a sustainable-finance framework with no fintech element. Kept in the clean set (155 records); Sean should decide.
- The Phase-2 agent used a different rule (inherited keyword block and no topic term) and reached the same 13 (`../bibliometrics/database-comparison.md`, section 3).

## A2. Table 1 (main information), raw versus clean
| | Raw 168 | Clean 155 |
|---|---|---|
| Documents | 168 | 155 |
| Sources | 77 | 77 |
| Articles / reviews | 138 / 30 | 137 / 18 |
| Distinct author names | 453 | 434 |
| Single-authored documents | 24 | 22 |
| Documents per year 2021-2026 | 3, 3, 18, 53, 75, 16 | 3, 3, 18, 53, 62, 16 |
| Mean citations per document | 22.55 (manuscript says 22.42) | 24.45 |
| Annual growth rate | 39.77 % | 39.77 % |
The growth rate is (16/3)^(1/5) - 1, that is it uses only the first year (3 records) and the part-year 2026 (16 records); cleaning does not change it because both end points are unaffected. The 0.13 difference in mean citations from the manuscript (22.42) is unexplained; the malformed row is the likeliest cause.

## A3. Table 2 (author keywords): artefacts (`table2_keywords.csv`)
Occurrences counted once per record. Raw to clean: fintech 107 to 94; green finance 107 to 94; **sustainable finance 23 to 10**; **AI finance 15 to 2; digital leadership 15 to 2; supply chain resilience 15 to 2**; sustainability 13 to 12; bibliometric analysis 12 to 10; systematic literature review 9 to 6. In the manuscript's Table 2 the three block keywords sit at ranks 7 to 9 and drive the text claims about "AI's growing role" and "post-pandemic sustainability concerns"; after cleaning they fall to 2 occurrences each.

## A4. Table 3 (countries, records per country counted once per record)
Raw top four reproduce the manuscript exactly (China 75, India 27, Malaysia 23, Saudi Arabia 20). The manuscript's table omits the United Arab Emirates (19 raw) and Jordan (9 raw); some lower counts differ by one or two (France 8 versus 9, Australia 6 versus 8; the manuscript's method may count differently). Clean: China 75, **Malaysia 23, Saudi Arabia 20, India 19 (down from 27)**, UAE 6 (down from 19), Pakistan 10, United Kingdom 10, Jordan 8, France 8, United States 6. India moves from second to fourth.

## A5. Table 4 corrected from the export (most-cited papers; `table4_comparison.csv`, `table4_corrected_top12.csv`)
Citation counts and years of all ten manuscript rows match the export. **Seven of ten source journals are wrong** and **seven titles differ from the export** (three only by shortening or a dropped word; four substantively).

| Rank | Title (as in export) | Year | Source (export) | Cited by | Manuscript said | DOI |
|---|---|---|---|---|---|---|
| 1 | The impact of fintech innovation on green growth in China: Mediating effect of green finance | 2022 | **Ecological Economics** | 512 | Resources Policy | 10.1016/j.ecolecon.2021.107308 |
| 2 | Nexus between green finance, fintech, and high-quality economic development: Empirical evidence from China | 2021 | Resources Policy | 386 | correct | 10.1016/j.resourpol.2021.102445 |
| 3 | Fintech and sustainability: Do they affect each other? | 2021 | Sustainability (Switzerland) | 292 | correct | 10.3390/su13137012 |
| 4 | The drivers of environmental sustainability in BRICS economies: Do green finance and fintech matter? | 2023 | **World Development Sustainability** | 204 | Sustainable Dev. | 10.1016/j.wds.2023.100096 |
| 5 | Green finance, fintech, and environmental sustainability: fresh policy insights from the BRICS nations | 2023 | **Int J Sustainable Development and World Ecology** | 178 | Finance Res. Lett. | 10.1080/13504509.2023.2183526 |
| 6 | The role of fintech in promoting green finance, and profitability: Evidence from the banking sector in the euro zone | 2023 | **Economic Analysis and Policy** | 139 | Resources Policy, title "Evidence from China" | 10.1016/j.eap.2023.02.001 |
| 7 | Striving for the United Nations (UN) sustainable development goals (SDGs) in BRICS economies: The role of green finance, fintech, and natural resource rent | 2023 | Sustainable Development | 109 | correct source, shortened title | 10.1002/sd.2618 |
| 8 | The fourth industrial revolution and environmental efficiency: The role of fintech industry | 2022 | **Journal of Cleaner Production** | 109 | Resources Policy, title altered | 10.1016/j.jclepro.2022.135196 |
| 9 | Empirical evidence of fintech and green environment: Using the green finance as a mediating variable | 2024 | **Int Rev of Economics and Finance** | 101 | Resources Policy, title altered | 10.1016/j.iref.2023.07.056 |
| 10 | Analysis of the carbon emission reduction effect of Fintech and the transmission channel of green finance | 2023 | **Finance Research Letters** | 96 | Resources Policy, title altered | 10.1016/j.frl.2023.104127 |
Ties: ranks 7 and 8 both have 109 citations; the export order places the journal-of-cleaner-production paper first. None of the ten is a series record, so the ranking itself is unchanged by cleaning. The manuscript sentence that Resources Policy is "the definitive outlet" rests on its own Table 5 (31 of 168 records), which is correct; but four of the ten top-cited papers it credits to Resources Policy are not in it. The text also calls rank 1 "the most-cited study (2022)" and names "Yang et al. (2021)" for rank 2: the export authors are Zhou G., Zhu J., Luo S. (rank 1) and Yang Y., Su X., Yao S. (rank 2).

## A6. Table 5 (sources) and authors
Review of Management Literature 15 to 2 (rank 2 to about rank 17); Resources Policy 31, Sustainability 13, Sustainable Development 10, Finance Research Letters 6 unchanged. "Rana S. leads with 15 papers" becomes 2; the next authors (Zhang Y. 4, Wang Y. 4, Tiwari S. 3, Xu J. 3, Udeagha M.C. 3) are unaffected.

## A7. References (`results/repair/reference_verdicts.csv`; Crossref checked 17 Oct 2026)
- **Do not resolve: 4** (R13 Khan, Yu, Sharif and Golpira 2022 ESPR; R14 Li, Du and Long 2023 JCP 382, 135245; R15 Xu, Chen and Zhao 2024 FRL 59, 104563; R17 Singh, Singh and Karmakar 2023 Library Philosophy and Practice). Probes: both DOIs implied by JCP 135245 return HTTP 404; FRL article 104563 is "The effects of financial frictions on Slovenian companies: A panel VAR approach"; the four authors of R13 have a 2020 panel-ARDL paper on SAARC countries in ESPR 27, 45675-45687, not a bibliometric analysis. Exact-title Crossref queries gave best matches of 0.45 to 0.80 similarity, all different papers; Semantic Scholar title match found none.
- **Unconfirmed: 1** (R9 Al Doghan and Chong 2023, IJOQM 29(2)): not in Crossref, which does not prove it does not exist.
- **Real but mis-cited: 2** (R16 Baas et al. is 2020, QSS 1(1):377-386, different title; R19 Gusenbauer is 2019, Scientometrics 118:177-214, not 2022 127(2)).
- **Resolve: 11** (R1-R8, R10, R11, R12); R18 duplicates R12.
- In-text citations absent from the list (`intext_vs_list.csv`, read by hand): Muganyi et al. 2021, Sanga and Aziakpono 2023, Aria and Cuccurullo 2017, Yang et al. 2021, Liu and You 2023, Hu et al. 2025. Listed but never cited in the text: Jia et al. 2025, Chien et al. 2025. Two reference styles are mixed.
- Not checked: whether the cited papers say what the text attributes to them. Nine of the resolving references were never opened by me.
- Note: Muganyi 2021 and Yang 2021, cited in the text but missing from the list, are the first two papers on the main citation path of the Phase-2 corpus (`depth/network/main_path_papers.csv`).

## A8. Other errors found
- Introduction: SDGs described as "building on" the Paris Agreement; the SDGs were adopted in September 2015, before Paris (December 2015).
- Method section: the final paragraph is a conclusion; no search string, no search date, no counts between 1,200 and 168 (rubric score 8/20, `results/rubric_scores_long.csv`).
- Table 5 gives the publisher of the series as "Various"; it is Emerald (export field Publisher: Emerald Publishing).
- The search string is not stored in the export. A reconstruction that all 168 records satisfy is `TITLE-ABS-KEY(fintech AND "green finance")` (Phase 2, `../bibliometrics/scopus-queries.md`); the manuscript's "1,200 publications" cannot be matched to it. 35 of 168 records match only through keywords rather than title or abstract (Phase 2 flag R0).

## A9. What to do next (no prose written)
- Re-run all tables from `results/repair/` clean data; decide on the shipping record; re-pull from Scopus with a recorded string and date (needs Dr Dhayal's or a library login).
- Rebuild the reference list only from papers opened; drop R13, R14, R15, R17 unless the papers can be produced.
