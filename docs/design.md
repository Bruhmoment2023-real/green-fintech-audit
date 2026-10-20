# 02 Design: reproducibility audit of green-fintech bibliometric reviews

Honesty note on order: the rubric items R1-R10 and the question list below were fixed before the five full texts were coded; one score changed after a second read (Fotova Cikovic et al., item R4, from 1 to 2, when the justification turned up in the limitations section). The prevalence test design was fixed before its run; the Semantic Scholar arm was cut to 7 queries by rate limits.

## Research questions
1. How completely do published bibliometric and systematic reviews at the green-finance by fintech intersection (2023-2026) report what a reader needs to re-run them (database, search string, date, limits, counts, cleaning, software versions, parameters, data)?
2. Which items are most often missing, and does reporting quality track outlet, database or year?
3. How often does book-series, proceedings or front-matter metadata contaminate topic searches on this subject, and does it depend on the database?
4. What did contamination do to one real corpus (the author's 168 Scopus records), and can the data be repaired?

## Hypotheses (directional, stated as expectations, not tested for significance with n = 5)
- H1: search date, cleaning method and data deposit are the least-reported items.
- H2: series-level metadata contamination exists in Scopus-style keyword matching and is rare in title-and-abstract engines.
- H3: top-ten tables (sources, keywords, countries) change more than the corpus size when 7.7 percent of records are removed.

## Data sources (access dates 2026-10-13 to 17)
- the author's Scopus export (March 2026, read only copy from E:). Licence: Scopus terms.
- The 15 reviews: Crossref and OpenAlex metadata (CC0); full text for 5 from open copies (MDPI CC BY, CEBR CC BY-NC-ND, EconStor CC BY, the author's own PDF).
- Guidelines: Europe PMC open-access XML, the author's PDF of Donthu et al.
- Prevalence: Crossref REST and Semantic Scholar Graph API (no key, no personal identifier), 50 queries (list in `code/prevalence.py`).
- Phase-2 corpus (OpenAlex rebuild, 497 records) read only for the wider-sample coding and the network analyses.

## Analysis plan
- Rubric: 0/1/2 anchors in `results/RUBRIC.md`; score from the text with a machine-checked quotation; NA where an item cannot apply; percent of applicable points; core score on the seven items the author listed.
- Second coder: regex detector vs manual "reported at all", raw agreement and kappa (sanity check only).
- Wider sample: abstract-level regex coding of 98 review-type records (database, number of records, period, software, protocol), hand spot-check of 10.
- Prevalence: per source, share of book/series/proceedings rows, share where all query terms occur only through the container title, front-matter title patterns, share lacking query terms in own title or abstract; hand labels on a random sample of 60 container-only book/proceedings records (95 percent normal-approximation interval).
- Repair: lexical flags plus hand screening of all 168 records; recompute Tables 1-5; compare Table 4 with the export; Crossref check of each reference with a second probe for failures.
- Phase 3: Kleinberg bursts (s=2, gamma=1) and search-path-count main path on the Phase-2 corpus.

## Threats to validity
- Single coder; five of fifteen full texts; abstract-level coding for nine; the rubric is adapted from BIBLIO, PRIBA, PRISMA-S and PRISMA 2020 (and GLOBAL was not readable); equal weights.
- The 15 reviews were chosen by Track B's search, which was itself incomplete; they include two that were found "using the same database and tools" as the author's, so the sample is not random.
- Prevalence depends on 50 queries, two APIs and one day; Semantic Scholar produced only 7 queries; Crossref's `query.bibliographic` is a fuzzy relevance search over bibliographic fields (not abstracts), so its raw book-chapter share is an artefact of that design and should not be read as "37 percent of the literature".
- Scopus could not be queried (no login), so the Scopus mechanism is shown only on the author's export and via the Phase-2 flags.
- Hand labels are by title and container, not by reading the chapters.
