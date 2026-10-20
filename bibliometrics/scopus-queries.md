# Scopus and Web of Science queries - task 10 (green fintech audit)

- `scopus-drop\` was **empty** on 13 Oct 2026. The only Scopus data here is Sean's own export
  (`data\raw\scopus\fntech green finance.csv`, file dated 22 Mar 2026, copied read-only from `E:\Downloads Copy\`).
- The export does **not store its search string**. The string below is reconstructed: all 168 valid records contain both
  `fintech` and `green finance` in title, abstract or keywords, the years run 2021-2026, and the document types are Article and
  Review. Sean should confirm it against his Scopus search history before quoting it in a paper.
- None of these strings has been run by the mapping agent (no Scopus/WoS access).

## 1. Reconstructed original search (Scopus)

```
TITLE-ABS-KEY ( fintech AND "green finance" )
AND PUBYEAR > 2020 AND PUBYEAR < 2027
AND ( DOCTYPE ( ar ) OR DOCTYPE ( re ) )
AND LANGUAGE ( english )
```

Expected on 22 Mar 2026: 168 records (after the filters). Run it again today and note the new count: the difference is the
seven-month growth, measured in the same database.

## 2. The same search without the keyword field (shows what the keyword field lets in)

```
TITLE-ABS ( fintech AND "green finance" )
AND PUBYEAR > 2020 AND PUBYEAR < 2027
AND ( DOCTYPE ( ar ) OR DOCTYPE ( re ) )
AND LANGUAGE ( english )
```

In the March export, 133 of 168 records satisfy this narrower string; 35 entered through keywords only, and 13 of those 35
are the contaminated book-series records (`tables\T01_scopus_record_flags.csv`).

## 3. Direct test of the contamination (Scopus)

```
SRCTITLE ( "Review of Management Literature" ) AND TITLE-ABS-KEY ( fintech AND "green finance" )
```

Expected: the 15 records of the Emerald series volume. Open two of them in Scopus and look at the Author keywords field:
the block `AI finance; Digital leadership; Fintech; Green finance; Supply chain resilience; Sustainable finance` is on every
chapter. A screenshot of that is the cleanest evidence for the audit paper.

## 4. Broader string used by several published reviews (for the audit's sensitivity check)

```
TITLE-ABS-KEY ( ( fintech OR "fin-tech" OR "financial technolog*" OR "digital finance" )
  AND ( "green finance" OR "green financ*" OR "sustainable finance" OR "climate finance" OR "green fintech" ) )
AND PUBYEAR > 2014 AND PUBYEAR < 2027
AND ( DOCTYPE ( ar ) OR DOCTYPE ( re ) )
AND LANGUAGE ( english )
```

## 5. Reviews to audit (bibliometric and systematic reviews of the topic)

```
TITLE-ABS-KEY ( ( fintech OR "financial technolog*" OR "digital finance" ) AND ( "green finance" OR "sustainable finance" OR "green fintech" )
  AND ( bibliometric* OR scientometric* OR "science mapping" OR "systematic literature review" OR "systematic review" OR vosviewer OR biblioshiny ) )
AND PUBYEAR > 2018
```

## Web of Science Core Collection equivalents

```
TS=( fintech AND "green finance" ) AND PY=(2021-2026) AND DT=(Article OR Review Article) AND LA=(English)
```

```
( TI=( fintech AND "green finance" ) OR AB=( fintech AND "green finance" ) ) AND PY=(2021-2026) AND DT=(Article OR Review Article) AND LA=(English)
```

```
TS=( ( fintech OR "fin-tech" OR "financial technolog*" OR "digital finance" ) AND ( "green finance" OR "green financ*" OR "sustainable finance" OR "climate finance" OR "green fintech" ) )
AND PY=(2015-2026) AND DT=(Article OR Review Article) AND LA=(English)
```

```
TS=( ( fintech OR "financial technolog*" OR "digital finance" ) AND ( "green finance" OR "sustainable finance" OR "green fintech" )
  AND ( bibliometric* OR scientometric* OR "science mapping" OR "systematic literature review" OR "systematic review" OR vosviewer OR biblioshiny ) )
AND PY=(2019-2026)
```

Notes:
- `TS=` in Web of Science also searches Keywords Plus, which are generated from cited titles. That is a second route by which
  off-topic records can enter a corpus; flag it with the same rule (`python\t10_01_scopus_flags.py` works on any Scopus CSV; for
  WoS adapt the column names).
- Web of Science Core Collection does not index the Emerald book series as journal articles, so the 13 contaminated records
  should be absent there. That contrast (present in Scopus, absent in WoS and OpenAlex title+abstract search) is worth one line
  in the audit.

## Loading exports

Drop CSV/BibTeX exports into `scopus-drop\`, then
`Rscript R/t10_03_scopus_M.R` (edit the file name at the bottom) and
`Rscript R/02_bibliometrix.R <file.rds> S2 DE "Scopus refresh" 2024`.
