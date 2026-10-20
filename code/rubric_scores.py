"""Hand-coded rubric scores for the reviews whose full text was opened (5 of the 15 + Sean's manuscript as a self-audit row).
Every evidence quote is machine-checked against the extracted text (whitespace, ligatures and quote marks normalised); the script
aborts if a quote is not found, so no quotation here can be invented. Page = PDF page index in the file I opened (not the journal's printed page).
Scores: 0 = not reported, 1 = partly / indirectly reported, 2 = reported so that a reader could re-run it. None = not applicable.
Output: results/rubric_scores_long.csv (one row per paper x item with evidence), results/rubric_scores_wide.csv"""
import re, os, csv, unicodedata, sys
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
FT = '../data/fulltext/'
def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"').replace('„', '"').replace('–', '-').replace('—', '-').replace('‚', "'")
    s = re.sub(r'(?<=\w)-\s+(?=\w)', '', s)    # pdf line-break hyphenation
    s = re.sub(r'[,\s]+', ' ', s)           # commas and whitespace collapse (pdf line-breaks insert spaces before commas)
    s = re.sub(r'\s+', ' ', s)
    return s.lower().strip()
def load(path):
    t = open(path, encoding='utf-8').read()
    parts = re.split(r'=====PAGE (\d+)=====', t)
    pages = {}
    if len(parts) > 1:
        for i in range(1, len(parts), 2): pages[int(parts[i])] = norm(parts[i + 1])
    else: pages[0] = norm(t)
    return pages
ITEMS = {
 'R1': 'Database(s) and platform named', 'R2': 'Search string reported as run (Boolean + field scope)', 'R3': 'Date the search was run',
 'R4': 'Limits and restrictions stated (with justification)', 'R5': 'Eligibility (inclusion/exclusion) criteria', 'R6': 'Record counts at each stage (flow)',
 'R7': 'Cleaning / screening steps described', 'R8': 'Software named with versions', 'R9': 'Analysis parameters (thresholds, normalisation, clustering)',
 'R10': 'Data and code shared'}
# paper -> item -> (score, quote or None, note)
S = {
 'R01 Kwong, Kwok, Wong 2023 (Sustainability)': ('review01', {
  'R1': (2, "we selected the Web of Science (WoS) Core Collection to conduct a keyword search for the literature", 'Names WoS Core Collection and four citation indexes.'),
  'R2': (1, "The keywords 'fintech' OR 'finance* technology' were used for the first set", 'Boolean terms given; no field tag (TS=, TITLE-ABS-KEY) and no single string as run.'),
  'R3': (1, "(accessed on 29 August 2023)", 'Only an access date attached to the data-availability URL; no statement that the search was run on that date.'),
  'R4': (2, "articles had to be published by 2022, written in English, and categorized under Business Finance, Management, Business, or Economics disciplines", 'All limits stated; the subject limit is justified by reference to Zhang et al. [27].'),
  'R5': (1, "We imposed specific criteria to identify relevant articles.", 'Criteria are database filters only; no relevance screening described.'),
  'R6': (1, "Ultimately, we obtained 776 articles on FinTech and 1428 articles on green finance or ESG", 'Final counts only; no flow diagram or intermediate counts.'),
  'R7': (0, None, 'No de-duplication, thesaurus or cleaning step described (text searched for duplicate, thesaurus, clean, merged).'),
  'R8': (1, "VOSviewer 1.6.18 was employed to develop and analyze the visualization networks", 'VOSviewer version given; Bibliometrix/Biblioshiny named without version.'),
  'R9': (2, "minimum threshold of five occurrences", 'Keyword and co-citation thresholds reported; clustering algorithm not named.'),
  'R10': (1, "Restrictions apply to the availability of these data.", 'Data statement points to WoS; no records or code deposited.')}),
 'R04 Saeedi, Ashraf 2024 (JRFM)': ('review04', {
  'R1': (2, "a thorough search was conducted on the following electronic databases: Scopus and Google Scholar", ''),
  'R2': (1, "The main keywords searched included Green Finance, Green Technology, Sustainability, Machine Learning", 'Keyword list only; no Boolean string; field scope stated in prose (title, abstract, complete text).'),
  'R3': (0, "The search was limited to the articles and research outputs from 2013 to 2024", 'Coverage period only; no search date.'),
  'R4': (1, "The search was limited to the articles and research outputs from 2013 to 2024", 'Limits stated (years, English, peer-reviewed in Table 1) but not justified.'),
  'R5': (2, "Table 1. Research evaluation criteria.", 'Inclusion/exclusion table given.'),
  'R6': (1, "Around 800 articles were screened using the inclusion and exclusion criteria", 'Approximate screened count and 90 included; no flow, no per-database counts.'),
  'R7': (0, None, 'No de-duplication or screening procedure (who, how) described.'),
  'R8': (None, None, 'Narrative synthesis; no software-based analysis reported (text searched for software, VOSviewer, Bibliometrix).'),
  'R9': (None, None, 'Not applicable (no network or thresholded analysis).'),
  'R10': (0, None, 'No data availability statement or supplementary material in the opened PDF.')}),
 'R06 Sethi, Mahadik 2024 (CEBR)': ('review06', {
  'R1': (2, "we gathered the data using the Scopus database", ''),
  'R2': (2, "uses the Boolean logic of \"AND\" in the title, abstract, and keyword", 'Two-term Boolean string with field scope in prose; Scopus syntax not shown.'),
  'R3': (1, "42 articles were produced up to the month of October 2023", 'Month of cut-off for the final year; no search date.'),
  'R4': (1, "The search was conducted from 2017 to 2023.", 'Years, document type, language and subject areas are in Figure 2 (image); no justification.'),
  'R5': (2, "Duplicates and those without author details are eliminated.", 'Inclusion/exclusion stated in text and Figure 2; text and figure disagree on document types (text excludes reviews; figure says Article).'),
  'R6': (1, "116 articles made up the final sample after all these criteria were applied", 'Two counts (215 retrieved, 116 final) in text and Figure 2; no intermediate counts.'),
  'R7': (1, "all of the results from the first search were verified twice to rule out any possible inconsistencies", 'Duplicate removal and double verification mentioned; no counts, no screener count, no tool.'),
  'R8': (1, "Wordstat, Biblioshiny, and VOSviewer are the programmes utilised for analysis", 'Names only; no versions.'),
  'R9': (2, "The minimal quantity of documents from a source (three) and the minimum quantity of citations from a source (two)", 'Thresholds reported for the networks shown.'),
  'R10': (0, None, 'No data availability statement in the opened PDF.')}),
 'R09 Zournatzidou 2025 (Administrative Sciences)': ('review09', {
  'R1': (2, "data were obtained from the Scopus database for the years 2019-2025", ''),
  'R2': (1, "AND (LIMIT-TO (SRCTYPE, \"j\"))", 'Table 1 prints ten successive Boolean strings; it is not stated which one returned the 945 records and no field code (TITLE-ABS-KEY) is shown.'),
  'R3': (0, "data were obtained from the Scopus database for the years 2019-2025", 'Coverage period only; no search date.'),
  'R4': (2, "The document categories are restricted to research papers", 'Limits shown in the final string (publication stage, source type) and justified as unity and consistency.'),
  'R5': (1, "(iv) geographic considerations, which encompass specific regions, states, countries, or populations", 'Four criteria listed but vague; how they were applied is not explained.'),
  'R6': (2, "The collection has a total of 945 sources, as determined by the search query.", 'Full PRISMA flow in Figure 1 (945, 80 duplicates, 82 other, 783, 124 by hand, 147 by Scopus, 512, 213 irrelevant, 299); arithmetic checks out.'),
  'R7': (1, "excluding those that were very vague or lacked a clear connection", 'Duplicate and exclusion counts are in the figure; no method, screener, or tool described.'),
  'R8': (1, "The R software (R 3.6.0+) offers sophisticated data analysis functionalities", 'Version given only as a minimum; "RStudio version 3.6.0 or above" is not a real RStudio version; VOSviewer unversioned.'),
  'R9': (0, None, 'Clustering and factorial analysis mentioned; no thresholds, minimum frequencies or cluster settings (text searched).'),
  'R10': (1, "Dataset available on request from the author.", '')}),
 'R10 Fotova Cikovic, Cvetkoska, Primorac 2025 (JRFM)': ('review10', {
  'R1': (2, "the authors utilized data from the Web of Science core collection, ESCI, SCI-EXPANDED and SSCI indexes", ''),
  'R2': (1, "with the keywords \"green finance\", \"green fintech\", \"sustainable finance\", \"climate finance\", and \"artificial intelligence\"", 'Five phrases with no operators and no field scope: AND or OR cannot be inferred (1261 hits).'),
  'R3': (2, "The survey and search of articles was initiated in June 2025", 'Month and year.'),
  'R4': (2, "This decision was made to maintain focus on the financial and economic dimensions of the green finance-AI nexus.", 'No time or document-type limit is stated; the WoS category filter (Business Economics) is justified in the limitations section, not in the methods.'),
  'R5': (1, "Thereafter, in the second phase, these documents were filtered by the WoS category Business Economics.", 'Only the category filter and (in Figure 2) a non-English exclusion; no stated criteria.'),
  'R6': (2, "The result was 1261 papers.", 'PRISMA flow (1261, 485 duplicates, 776, 131, 645, 282, 363, 95, 268); arithmetic checks out but the text says the 268 came from the category filter, the figure says from duplicate and retrieval exclusions.'),
  'R7': (1, "a qualitative cleaning process was applied, excluding general or redundant terms", 'Term-level cleaning described; record-level de-duplication (485 of 1261 from one database) has no method.'),
  'R8': (2, "Analyses were conducted using the Bibliometrix 5.1.0 R package", 'Bibliometrix 5.1.0 and VOSviewer 1.6.20 (abstract).'),
  'R9': (2, "only terms occurring at least five times were retained, yielding 1710 terms", 'Also top 60 percent by relevance score (1026 terms).'),
  'R10': (1, "Data is available on request.", 'PRISMA checklist offered as a supplement; no records or code.')}),
}
# Sean's manuscript (24 May 2026) - self-audit row; quotes checked against the docx text
MS = {
 'R1': (2, "Scopus was selected because it is one of the most comprehensive and reliable databases", ''),
 'R2': (1, "The search was conducted using keywords such as", 'Keywords "such as" green finance and Fintech; no string, no field tags.'),
 'R3': (0, None, 'No search date anywhere in the text (data stated "until 2026"; Table 2 note says March 2026 for partial-year data).'),
 'R4': (1, "Only English-language publications were analysed", 'English and journal articles/reviews stated (limitations, method); not justified.'),
 'R5': (1, "the titles and abstracts of the remaining papers were reviewed to exclude studies that were not directly related", 'Criterion stated in one sentence; contradicted by the data (13 off-topic records remain).'),
 'R6': (1, "The initial search in Scopus returned 1,200 publications.", '1,200 and 168 only; no intermediate counts.'),
 'R7': (1, "First, duplicate records were removed.", 'Steps listed without counts, screener or tool; the claimed screening did not remove the series records.'),
 'R8': (1, "Analysis performed using Bibliometrix R package and VOSviewer 1.6.18.", 'VOSviewer versioned; Bibliometrix not.'),
 'R9': (0, None, 'No thresholds, minimum occurrences or clustering settings.'),
 'R10': (0, None, 'No data statement.')}

rows = []; wide = {}
bad = []
for paper, (fkey, items) in S.items():
    pages = load(FT + fkey + '.txt')
    for it, (sc, q, note) in items.items():
        page = ''
        if q:
            nq = norm(q); hit = [p for p, tx in pages.items() if nq in tx]
            if not hit:
                # quote may straddle a page break: test on concatenation
                allt = ' '.join(pages[p] for p in sorted(pages))
                if nq in allt: hit = ['straddles page break']
                elif nq.replace(' ','') in allt.replace(' ',''): hit = ['(matched ignoring pdf spacing)']
                else: bad.append((paper, it, q));
            page = ','.join(str(h) for h in hit)
        rows.append(dict(paper=paper, item=it, item_name=ITEMS[it], score=sc, evidence_quote=q or '', pdf_page=page, note=note))
        wide.setdefault(paper, {})[it] = sc
# manuscript
import zipfile, html
z = zipfile.ZipFile('../data/source/manuscript_2026-05-24.docx'); x = z.read('word/document.xml').decode('utf8')
x = re.sub(r'</w:p>', '\n', x); x = re.sub(r'<[^>]+>', '', x); mt = norm(html.unescape(x))
paper = 'S0 Sean manuscript 24 May 2026 (self-audit, not one of the 15)'
for it, (sc, q, note) in MS.items():
    if q and norm(q) not in mt: bad.append((paper, it, q))
    rows.append(dict(paper=paper, item=it, item_name=ITEMS[it], score=sc, evidence_quote=q or '', pdf_page='docx text' if q else '', note=note))
    wide.setdefault(paper, {})[it] = sc
if bad:
    for b in bad: print('QUOTE NOT FOUND', b)
    sys.exit('fix quotes before writing')
os.makedirs('../results', exist_ok=True)
with open('../results/rubric_scores_long.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open('../results/rubric_scores_wide.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['paper'] + list(ITEMS) + ['total_scored', 'max_applicable', 'pct', 'core6_pct'])
    core = ['R1', 'R2', 'R3', 'R6', 'R7', 'R8', 'R10']   # search string, db+date, counts, cleaning, software, data: the six things Sean listed (R1+R3 = database and date)
    for p, d in wide.items():
        app = [k for k, v in d.items() if v is not None]
        tot = sum(d[k] for k in app); mx = 2 * len(app)
        ca = [k for k in core if d[k] is not None]
        w.writerow([p] + [d[k] if d[k] is not None else 'NA' for k in ITEMS] + [tot, mx, round(100 * tot / mx, 1), round(100 * sum(d[k] for k in ca) / (2 * len(ca)), 1)])
        print(p, '|', [d[k] for k in ITEMS], tot, '/', mx, round(100 * tot / mx, 1), '| core', round(100 * sum(d[k] for k in ca) / (2 * len(ca)), 1))
print('all quotes verified in source text:', len(rows), 'rows')
