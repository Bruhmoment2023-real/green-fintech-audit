# Search protocol - 10 Green fintech: Scopus export versus OpenAlex / Crossref rebuild (database-comparison audit)

- **Date of search:** 2026-10-13 (UTC). Years covered: 2021-2026 (2026 incomplete).
- **Who screened:** rule-based screening by the regular expressions below, followed by a hand check of titles by the mapping agent (an AI assistant), not by a human reviewer. Sean should re-screen the core set himself before citing counts.
- **No API keys, no logins.** Every response is cached in `data/raw/`.

## 1. Databases and what each was used for

- Scopus: Sean's own export (`data/raw/scopus/fntech green finance.csv`, dated 2026-03-22, 169 rows, 168 valid), loaded into Bibliometrix with dbsource = "scopus". No Scopus login was available here.
- OpenAlex: true title-and-abstract search (574 hits, basic paging) plus single-work lookups by DOI for candidates found elsewhere; merged and filtered with the same string rule. Anonymous quota was exhausted on 2026-10-13 and reset later; requests were slow, cached and carry no personal identifier.
- Semantic Scholar Graph API (Boolean title+abstract search) and Crossref (free text, journal articles) as candidate discovery routes and for the Crossref comparison corpus.
- Web of Science: no access; strings in scopus-queries.md.

## 2. Exact search strings and hits

### Semantic Scholar bulk search (title + abstract; `+` = AND, `|` = OR; year filter 2021-2026)

| Tag | Sub-literature | Query | Hits reported | Records taken |
|---|---|---|---|---|
| S0 | - | `fintech + "green finance"` | 434 | 434 |
| S1 | - | `(fintech \| "fin-tech" \| "financial technology" \| "financial technologies") + ("green finance" \| "green financing")` | 497 | 497 |

### Crossref `query.bibliographic` (relevance-ranked free text, no Boolean; top results taken per string, then screened locally)

| Tag | Sub-literature | Query | Hits reported | Records taken |
|---|---|---|---|---|
| C0 | - | `fintech green finance` | 505701 | 1000 |
| C1 | - | `financial technology green finance` | 2380606 | 1000 |
| C2 | - | `green fintech` | 352422 | 1000 |
| C3 | - | `fintech green finance carbon emissions` | 951823 | 1000 |
| C4 | - | `fintech green finance sustainable development` | 2346120 | 1000 |
| C5 | - | `fintech green finance natural resources` | 1006949 | 1000 |
| C6 | - | `digital finance green finance fintech` | 1258658 | 1000 |
| C7 | - | `fintech green finance bibliometric review` | 3292769 | 1000 |

## 3. Inclusion rules (applied to title + abstract, case-insensitive)

A record is included if it matches **at least one** sub-literature rule. Within a rule every numbered group must match.

**L. Reviews and bibliometric studies**
  1. `\b(bibliometric\w*|scientometric\w*|systematic (literature )?review|literature review|scoping review|science mapping|state of the art of the literature|research agenda)\b`

**E. Carbon emissions / environmental quality**
  1. `\b(carbon|co2|emissions?|environmental (quality|degradation|sustainability|performance|pollution|governance)|ecological footprint|climate|pollut\w+)\b`

**R. Natural resources / energy**
  1. `\b(natural resources?|resource (curse|rents?|efficiency|extraction|dependence)|minerals?|renewable energy|energy (transition|efficiency|consumption|poverty))\b`

**I. Green innovation / firms / ESG**
  1. `\b(green (innovation|technolog\w+|patents?)|corporate|firms?|enterprises?|esg|smes?)\b`

**B. Banking, credit, bonds, investment**
  1. `\b(bank\w*|green (credit|bonds?|loans?|invest\w+)|lending|credit)\b`

**D. Digital technology (AI, blockchain, digital finance)**
  1. `\b(blockchain|artificial intelligence|machine learning|big data|digital (finance|economy|transformation|inclusive finance)|financial inclusion)\b`

**Z. Other / none of the coded themes**
  1. `(?!x)x`

## 4. Exclusion rules

- Publication year outside 2021-2026.
- No sub-literature rule matched on title + abstract (the database search engines match more loosely than the rules).
- Hand screen: records listed in `data/clean/excluded_manual.csv`, each with its reason.
- Versions: a preprint and its published version are one record (merged by Semantic Scholar paper ID, DOI, arXiv ID, ACL ID, then by normalised title + first-author surname).

## 5. Snowballing (one round)

- Not run for this corpus (see README).

## 6. PRISMA-style counts (OpenAlex corpus; Scopus corpus in the second table)

| Step | Records |
|---|---|
| Candidate DOIs from Semantic Scholar, Crossref and the Scopus export (Crossref pre-filtered) | 3,149 |
| OpenAlex true search hits (title+abstract, 2021-2026, article or review) | 574 |
| OpenAlex works fetched, all candidates | 3,241 |
| Matching the string `fintech AND "green finance"` in OpenAlex title+abstract | 611 |
| After English, article/review, 2021-2026 and title de-duplication | **497** (360 on or before the Scopus export date) |
| Removed in hand screen | 0 (the string rule on title+abstract is the only screen; no title-level hand screen was done for this corpus) |

| Scopus step | Records |
|---|---|
| Rows in export | 169 |
| Malformed row dropped | 1 |
| Valid records | 168 |
| Contaminated (rule R1 and R2, see database-comparison.md) | 13 |
| Cleaned corpus | **155** |

## 7. Coverage of the final corpus

| Field | Documents | Share |
|---|---|---|
| with abstract | 457 | 92.0% |
| with reference list | 224 | 45.1% |
| with openalex record | 497 | 100.0% |
| with institution | 405 | 81.5% |
| with country | 400 | 80.5% |
| with openalex keywords | 496 | 99.8% |
| with doi | 457 | 92.0% |

- Reference links: 12932 in total, 611 point to another corpus document.
- By sub-literature (a document can match several): None
- By document type: {'article': 470, 'review': 27}

## 8. Limits

