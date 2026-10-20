"""Generates depth/appendix/data-dictionary.md: for each data/result file the path, rows, columns and (hand-written) meaning.
Row and column counts are read from the files at run time."""
import os, csv, json, glob, datetime
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FILES = {
 'data/source/scopus_export_original.csv': ('Sean\'s Scopus export, byte copy of E:\\Downloads Copy\\fntech green finance.csv (file dated 2026-03-22)', 'Scopus CSV columns (75, many empty); one record is split over two rows by a line break inside a References field; Year column of the broken row holds page text.'),
 'data/source/manuscript_2026-05-24.docx': ('Copy of "Fintech Manuscrip Final (1).docx" (saved 24 May 2026)', 'Binary; text extracted on the fly.'),
 'data/scopus_export_flags.csv': ('Export with my flags (row = spreadsheet row, has_fin_ta, has_grn_ta, has_ft_ta, has_gf_ta, series, lexical_core)', 'Flags are lexical tests on title+abstract; lexical_core False for 15 records (14 series, 1 shipping).'),
 'data/reviews15_meta.csv': ('Crossref and OpenAlex metadata for the 15 reviews, retrieved 2026-10-17', 'oa_status, oa_url, best_pdf from OpenAlex; n_refs_crossref is the reference count Crossref holds.'),
 'data/reviews15_abstracts.json': ('Abstracts of the 15 reviews from OpenAlex (inverted index rebuilt) and Semantic Scholar where available', 'Empty string = no abstract found.'),
 'data/prevalence/search_records.csv': ('Rows returned by 50 topic queries on Crossref (top 100 each) and Semantic Scholar (first 7 queries), 2026-10-17', 'src; q; id (DOI); title; year; venue (container/venue); rtype (journal, proceedings, book/series, other:*); has_abstract; query_terms_in_own_title_abstract; terms_only_via_container (Crossref); front_matter.'),
 'results/rubric_scores_long.csv': ('One row per paper x rubric item with score, verbatim evidence quote, PDF page and note', 'score 0/1/2 or empty for not applicable; quotes machine-checked.'),
 'results/rubric_scores_wide.csv': ('Scores by paper (R1-R10), total, maximum, percent, core percent', 'NA = not applicable.'),
 'results/auto_vs_manual.csv': ('Regex detector versus manual "reported at all" per paper and item', 'agree = detector and manual coincide.'),
 'results/wide_sample_abstract_coding.csv': ('Regex coding of abstracts of 98 review-type records from the Phase-2 corpus', 'A1 database, A2 number of records, A3 period, A4 software, A5 protocol; is_bibliometric.'),
 'results/series_other_databases.csv': ('Crossref and OpenAlex metadata for the 15 series records', 'openalex_keywords are OpenAlex\'s own; flags test for the volume keyword block.'),
 'results/prevalence_hand_labelled_sample.csv': ('60 random Crossref book/proceedings records (container-only matches) with my hand label', 'F front/back matter, G generic or unrelated, B borderline, R relevant.'),
 'results/repair/screening_decisions.csv': ('Include/exclude/borderline decision for each of the 168 export records with reason', ''),
 'results/repair/table2_keywords.csv': ('Keyword counts raw and clean', ''),
 'results/repair/table3_countries.csv': ('Records per country raw and clean (one count per record)', ''),
 'results/repair/table4_comparison.csv': ('Manuscript Table 4 rows against the export (title similarity, source ok, citations ok)', ''),
 'results/repair/table4_corrected_top12.csv': ('Corrected top-cited list from the cleaned export', ''),
 'results/repair/reference_check_crossref.csv': ('Best Crossref match for each of the 19 manuscript references', 'title_similarity is difflib ratio.'),
 'results/repair/reference_verdicts.csv': ('Hand verdict per reference (resolves, does not resolve, mis-cited, unconfirmed)', ''),
 'results/repair/intext_vs_list.csv': ('In-text author-year citations versus the reference list (regex; checked by hand)', 'The regex misses some citation forms; the final list is in the repair appendix.'),
 'depth/network/keyword_bursts.csv': ('Kleinberg bursts per OpenAlex keyword', 'weight = summed cost difference over the burst years.'),
 'depth/network/main_path_papers.csv': ('Papers on the global main path in citation order', 'on_keyroute flag.'),
 'depth/network/key_route_papers.csv': ('Papers on key routes', ''),
 'depth/network/data/snapshot_master.csv': ('Copy of the Phase-2 corpus (497 OpenAlex records) taken on the run date', 'See bibliometrics/ for its own documentation.'),
 'depth/network/data/snapshot_references.csv': ('Copy of Phase-2 reference links (citing, cited OpenAlex ids)', ''),
 'depth/citations/references.bib': ('BibTeX from Crossref', ''),
}
out = ['# Data dictionary (pack 10)', '', f'Generated {datetime.date.today()} by `code/build_appendix.py`; counts read from the files. "Known problems" lists what I know is wrong or limited.', '',
       '| Path | Source and date | Rows | Columns | Meaning of variables and known problems |', '|---|---|---|---|---|']
for rel, (src, note) in FILES.items():
    p = os.path.join(ROOT, rel); rows = cols = ''
    if not os.path.exists(p): out.append(f'| {rel} | MISSING | | | |'); continue
    try:
        if rel.endswith('.csv'):
            d = pd.read_csv(p, dtype=str, on_bad_lines='skip', encoding='utf-8-sig'); rows, cols = len(d), '; '.join(d.columns[:14]) + (' ...' if d.shape[1] > 14 else '') + f' ({d.shape[1]})'
        elif rel.endswith('.json'): j = json.load(open(p, encoding='utf-8')); rows, cols = len(j), 'dict of items'
        elif rel.endswith('.bib'): rows, cols = open(p, encoding='utf-8').read().count('\n@'), '-'
    except Exception as e: rows, cols = 'err', str(e)[:60]
    out.append(f'| {rel} | {src} | {rows} | {cols} | {note} |')
out += ['', '## Text copies (data/fulltext/*.txt)', 'Extracted text (pypdf or Europe PMC XML) of the PDFs and articles I opened: review01/04/06/09/10, guideline_biblio/prismas/prisma2020, donthu2021, baas2020, gusenbauer2019/2020, zupic2015, ellegaard2015, arxiv2508_16276, koo2023_priba. Source PDFs are in E:\\Research-Staging\\10-green-fintech-audit\\pdfs\\ (see STAGING.md). Known problems: pypdf drops some figure text and splits words at line breaks; quotations are checked with whitespace, hyphenation and ligature normalisation. Copyright: texts are for local analysis only and are not redistributed.', '',
        '## HTTP cache', 'data/cache/http.sqlite holds every API response (200 and 404 only) so re-runs are deterministic for the dates shown; it is a cache, not a deliverable.']
open(os.path.join(ROOT, 'depth/appendix/data-dictionary.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n'); print('ok', len(FILES))
