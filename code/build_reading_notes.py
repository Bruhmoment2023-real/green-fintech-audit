"""Builds depth/reading-notes/*.md. Every verbatim quotation is machine-checked against the extracted text (pdf page numbers are PDF page indices
in the file I opened; Europe PMC texts have no pages). Everything else in a note is my summary of passages I read; where a section was not read it says so."""
import re, os, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
OUT = '../depth/reading-notes/'; os.makedirs(OUT, exist_ok=True)
def norm(s):
    s = unicodedata.normalize('NFKC', s)
    for a, b in {'‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-', '‐': '-', '‑': '-'}.items(): s = s.replace(a, b)
    s = re.sub(r'(?<=\w)-\s+(?=\w)', '', s); s = re.sub(r'[,\s]+', ' ', s)
    return s.lower().strip()
def pages_of(path):
    t = open(path, encoding='utf-8', errors='replace').read(); parts = re.split(r'=====PAGE (\d+)=====', t)
    if len(parts) == 1: return {0: norm(t)}
    return {int(parts[i]): norm(parts[i + 1]) for i in range(1, len(parts), 2)}
N = []  # notes
def note(fn, text, cite, link, access, rq, data, method, results, limits, quotes, bears):
    N.append(dict(fn=fn, text=text, cite=cite, link=link, access=access, rq=rq, data=data, method=method, results=results, limits=limits, quotes=quotes, bears=bears))

note('kwong-2023-greenfintech', 'review01', 'Kwong R, Kwok MLJ, Wong HSM (2023). Green FinTech innovation as a future research direction: a bibliometric analysis on green finance and FinTech. Sustainability 15(20):14683.',
 'https://doi.org/10.3390/su152014683', 'opened in full (27 pages; Sean\'s own PDF is byte-identical)',
 'Four questions: how the green finance and FinTech literatures evolve; which topics and how organised; which countries the authors come from; what synergies exist between the two.',
 'Web of Science Core Collection (SSCI, SCIE, ESCI, AHCI), English, published by 2022, categories Business Finance, Management, Business, Economics. Two sets: 776 FinTech articles and 1,428 green finance/ESG articles.',
 'Bibliometric performance analysis and science mapping with Bibliometrix/Biblioshiny and VOSviewer 1.6.18; co-citation clusters; qualitative cluster reading. Descriptive: no causal design.',
 'Counts above; FinTech output grows at an annual 38.54 percent; keyword and co-citation thresholds of five occurrences (keywords) and a stated minimum for cited references. I did not read the cluster discussion in detail (sections 3.2 to 3.7 skimmed only).',
 'Data statement says restrictions apply to the data (Web of Science licence). I did not find a limitations section that discusses search reproducibility.',
 ['we selected the Web of Science (WoS) Core Collection to conduct a keyword search for the literature', 'We imposed specific criteria to identify relevant articles.', 'Ultimately, we obtained 776 articles on FinTech and 1428 articles on green finance or ESG', 'This led to a 38.54% annual growth rate for FinTech publications.', 'Restrictions apply to the availability of these data.'],
 'Method to borrow and a template Sean followed (database, tools, section layout). Contradicts nothing, but it is the paper whose reporting gaps Sean inherited: no search date, no cleaning step, no counts per stage. Rubric 12/20 (60 percent).')

note('saeedi-2024-technology', 'review04', 'Saeedi M, Ashraf BN (2024). The role of technology in promoting green finance: a systematic literature survey and the development of a framework. J Risk Financial Manag 17(10):472.',
 'https://doi.org/10.3390/jrfm17100472', 'opened in full (14 pages, CC BY)',
 'The role of technology in developing green finance; three challenges (risk management of green projects, lack of innovation in green financing products, regulatory compliance) and how technologies address them.',
 'Scopus and Google Scholar, 2013-2024, English, peer reviewed; around 800 articles screened, 90 articles, reports and research outputs selected; Table 2 lists the 90 by venue.',
 'Narrative systematic literature survey with an inclusion/exclusion table (Table 1) and a thematic grouping (Table 3). No bibliometric software.',
 '90 sources, grouped into five areas (33 green finance/technology/sustainability; 12 ML, AI, risk management; 19 financing products and crowdfunding; 15 regulatory compliance; 11 cryptocurrencies), per Table 3.',
 'I found no limitations paragraph about the search in the parts I read (sections 1-3 and conclusion skimmed).',
 ['we conduct a systematic literature survey to examine the role of technology in the development of green finance', 'Around 800 articles were screened using the inclusion and exclusion criteria', 'To the best of our knowledge, this is the first-ever attempt to understand the role of different technologies in green finance'],
 'Different design (survey, not bibliometric) but scored on the search items. Includes conference papers, working papers and a Research Square preprint among the 90, so "peer-reviewed" in Table 1 is not what the list shows (Table 2 includes "Research Square" and "McKinsey & Company"). Rubric 7/16 (43.8 percent).')

note('sethi-2024-fintech-sustainability', 'review06', 'Sethi M, Mahadik S (2024). Exploring the interrelation: bibliometric analysis and systematic review of fintech and sustainability. Central European Business Review 13(5).',
 'https://doi.org/10.18267/j.cebr.368', 'opened in full (41 pages, CC BY-NC-ND; Figure 2 viewed as an image)',
 'Six research questions on the intellectual landscape of fintech and sustainability research (productive authors, sources, most cited work, themes, gaps).',
 'Scopus, "Fintech" AND "Sustainability" in title, abstract and keywords; 215 retrieved, 116 final; 2017-2023 (2023 up to October).',
 'Bibliometric analysis (Biblioshiny, VOSviewer, WordStat) plus a systematic review; PRISMA-labelled flowchart (Figure 2) with year range, subject areas, article-only and English-only filters.',
 'Annual output rises from 2 articles in 2017 to 42 in 2023 (to October). Thresholds: minimum three documents and two citations per source for the coupling map; keyword threshold of 20 in the Biblioshiny table.',
 'States that the study looks solely at Scopus and that the query used general terms (title, abstract, keywords); recommends other databases and richer term combinations.',
 ['"Fintech" AND "Sustainability" are the keywords employed in this study.', '116 articles made up the final sample after all these criteria were applied', '42 articles were produced up to the month of October 2023', 'This research solely looks at the Scopus database.'],
 'Closest in style to Sean\'s manuscript (Scopus, two broad terms). Positive example for R2 and R9. Text and Figure 2 disagree on which document types were kept. Rubric 13/20 (65 percent).')

note('zournatzidou-2025-greentech', 'review09', 'Zournatzidou G (2025). Green finance and sustainable development: investigating the role of greentech business ecosystem through PRISMA-driven bibliometric analysis. Administrative Sciences 15(4):150.',
 'https://doi.org/10.3390/admsci15040150', 'opened in full (EconStor copy, 25 pages, CC BY; Figure 1 viewed as an image)',
 'Research trends on green finance, sustainability and the move from fintech to greentech.',
 'Scopus, 2019-2025; PRISMA flow 945 identified, 80 duplicates and 82 other removed, 783 screened, 124 excluded by hand and 147 by Scopus functionality, 512 assessed, 213 irrelevant, 299 included.',
 'Bibliometrics with Biblioshiny and VOSviewer; ten stepwise Boolean strings in Table 1; factorial (correspondence) analysis.',
 'Flow arithmetic checks out. Final corpus 299. I did not read the results sections beyond the first pages.',
 'I located no limitations statement.',
 ['The collection has a total of 945 sources, as determined by the search query.', 'A total of 299 academic articles were found and included in the bibliometric study using this screening method.', 'The search criteria were modified to focus on research pertinent to the present study and to exclude extraneous references.', 'Dataset available on request from the author.'],
 'Best flow diagram of the five but the string that produced 945 is not identified, there is no search date, and "R 3.6.0+" and "RStudio version 3.6.0 or above" are not versions of the tools used. Rubric 11/20 (55 percent).')

note('fotova-2025-greenfinance-ai', 'review10', 'Fotova Cikovic K, Cvetkoska V, Primorac D (2025). The nexus between green finance and artificial intelligence: a systemic bibliometric analysis. J Risk Financial Manag 18(8):420.',
 'https://doi.org/10.3390/jrfm18080420', 'opened in full (19 pages, CC BY; Figures 1 and 2 viewed as images)',
 'Key trends, themes and contributors in green finance and AI; evolution of approaches; underexplored areas.',
 'Web of Science Core Collection (ESCI, SCIE, SSCI), search initiated June 2025, all years; 1,261 records, 268 after filtering; Bibliometrix 5.1.0 and VOSviewer 1.6.20.',
 'Bibliometric and co-occurrence analysis plus a systematic review with a PRISMA 2020 flow diagram (Figure 2); term thresholds (at least five occurrences, 1,710 terms; top 60 percent by relevance, 1,026 terms) and qualitative term cleaning.',
 'Annual growth rate 53.31 percent (abstract). Flow arithmetic checks out; the text and the figure give different routes from 1,261 to 268.',
 'Limitations: Web of Science only; Business Economics category filter excludes environmental science, computer science and engineering work (the authors say the filter was chosen to keep a financial focus); English bias.',
 ['The survey and search of articles was initiated in June 2025', 'The result was 1261 papers.', 'only terms occurring at least five times were retained, yielding 1710 terms.', 'This decision was made to maintain focus on the financial and economic dimensions of the green finance-AI nexus.', 'Data is available on request.'],
 'Most complete reporting of the five (80 percent): the model for date, versions and thresholds. Also a green-finance by AI review with a search phrase list that has no operators. A 2025 competitor in the saturated field.')

note('montazeri-2023-biblio', 'guideline_biblio', 'Montazeri A, Mohammadi S, M.Hesari P, Ghaemi M, Riazi H, Sheikhi-Mobarakeh Z (2023). Preliminary guideline for reporting bibliometric reviews of the biomedical literature (BIBLIO): a minimum requirements. Systematic Reviews 12:239.',
 'https://doi.org/10.1186/s13643-023-02410-2', 'opened in full (Europe PMC PMC10722750; no page numbers in the XML)',
 'A minimum reporting checklist for bibliometric reviews.', 'Literature review of methodological papers (13,720 identified, 19 relevant after de-duplication) and a four-round Delphi with eleven experts.',
 'Delphi consensus (cut-off 75 to 80 percent agreement), registered with the EQUATOR Network.',
 '20 items: title 2, abstract 1, introduction 2, methods 7, results 4, discussion 4. Methods items: information sources, search strategy (keywords, date of search, language, document type), time period, eligibility, data refinement, optional quality assessment, data synthesis.',
 'The authors say the guideline is preliminary and that "there is no evidence" it improves quality; the full item explanations were still "in progress" in the paper.',
 ['The BIBLIO includes 20 items as follows: title (2 items), abstract (1 item), introduction/background (2 items), methods (7 items), results (4 items), discussion (4 items).', 'The BIBLIO checklist was registered in the EQUATOR Network on 19 October 2021', 'there is no evidence to suggest it will improve the quality of bibliometric reviews'],
 'Primary source for rubric items R1-R7 and R9. Aimed at biomedical reviews; Sean should say it is adapted, and that BIBLIO has nothing on software versions or data sharing.')

note('rethlefsen-2021-prisma-s', 'guideline_prismas', 'Rethlefsen ML, Kirtley S, Waffenschmidt S, Ayala AP, Moher D, Page MJ, Koffel JB, PRISMA-S Group (2021). PRISMA-S: an extension to the PRISMA statement for reporting literature searches in systematic reviews. J Med Libr Assoc 109(2).',
 'https://doi.org/10.5195/jmla.2021.962', 'opened in full (Europe PMC PMC8270366; no page numbers in the XML)',
 'Reporting items so that a literature search can be understood and repeated.', 'Delphi and consensus process described in the paper (I did not read those sections).', 'Checklist of 16 items.',
 'Items include database name with platform (1), full search strategies as run (8), limits with justification (9), dates of searches (13), total records per source (15) and the method and software for de-duplication (16).',
 'Written for health-science systematic reviews; applying it to economics keyword searches is an adaptation.',
 ['Include the search strategies for each database and information source, copied and pasted exactly as run.', 'For each search strategy, provide the date when the last search occurred.', 'Describe the processes and any software used to deduplicate records from multiple database searches and other information sources.'],
 'Primary source for rubric items R1-R4, R6, R7 (search-level). Also the answer to "which published checklist did you adapt?" in a viva.')

note('page-2021-prisma2020', 'guideline_prisma2020', 'Page MJ, McKenzie JE, Bossuyt PM, et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ 372:n71.',
 'https://doi.org/10.1136/bmj.n71', 'opened in full (Europe PMC PMC8005924; no page numbers); I read the checklist table only',
 'Updated reporting guideline for systematic reviews.', 'n/a for this note.', 'n/a.', '27-item checklist; item 5 eligibility criteria, item 16a flow of records, item 27 availability of data, code and other materials.', 'Not read beyond the checklist.',
 ['Report which of the following are publicly available and where they can be found: template data collection forms; data extracted from included studies; data used for all analyses; analytic code; any other materials used in the review.'],
 'Source for rubric R5, R6 (flow), R10 (data and code). Also the standard for the Pack 14 meta-analysis.')

note('donthu-2021-howto', 'donthu2021', 'Donthu N, Kumar S, Mukherjee D, Pandey N, Lim WM (2021). How to conduct a bibliometric analysis: an overview and guidelines. J Bus Res 133:285-296.',
 'https://doi.org/10.1016/j.jbusres.2021.04.070', 'opened in full (Sean\'s own PDF "Base article.pdf" on E:, read only; 12 pages)',
 'How to plan, collect, analyse and report a bibliometric analysis.', 'Illustrated with a Scopus search for "bibliom*" (title, abstract, keywords) in business, economics and social sciences.',
 'Four-step workflow ending in a checklist (define aims, choose techniques, collect data, run analysis and report).',
 'Step 3 checklist asks whether search terms exemplify the scope, whether database coverage is adequate, whether the data are free of duplicates and erroneous entries, and whether the dataset fits the chosen techniques.',
 'Notes that Scopus and Web of Science data are not produced for bibliometric analysis and contain errors that must be cleaned.',
 ['Is the data free of errors such as duplicates and erroneous entries?', 'scholars should remove duplicates and erroneous entries', 'the paper\'s recommendation is to settle on one appropriate database to mitigate the need for that consolidation'],
 'The paper Sean already holds; it says to clean the data, which his manuscript did not do for the 13 series records. Source for R7.')

note('baas-2020-scopus', 'baas2020', 'Baas J, Schotten M, Plume A, Cote G, Karimi R (2020). Scopus as a curated, high-quality bibliometric data source for academic research in quantitative science studies. Quantitative Science Studies 1(1):377-386.',
 'https://doi.org/10.1162/qss_a_00019', 'opened in full (CC BY; 10 pages). Sean\'s manuscript cites it as 2021, QSS 2(1): the year and volume are wrong.',
 'Describes Scopus content selection, quality assurance, author and institution profiling.', 'Scopus itself.', 'Descriptive account by the database owner.',
 'Scopus holds over 76 million records at the time of writing, from over 39,100 serial titles (figures in section 1).',
 'None read that concern keyword contamination of book series.',
 ['Scopus is among the largest curated abstract and citation databases', '1Elsevier B.V., Radarweg 29, Amsterdam, The Netherlands'],
 'Authors are employees of the company that owns Scopus: cite it for what Scopus says about itself, not as independent evidence that Scopus is high-quality. It does not address the series-metadata problem found in Sean\'s export.')

note('gusenbauer-2020-search-systems', 'gusenbauer2020', 'Gusenbauer M, Haddaway NR (2020). Which academic search systems are suitable for systematic reviews or meta-analyses? Evaluating retrieval qualities of Google Scholar, PubMed, and 26 other resources. Research Synthesis Methods 11(2):181-217.',
 'https://doi.org/10.1002/jrsm.1378', 'opened in full (Europe PMC PMC7079055; no page numbers); abstract and the summary paragraph read, tables not studied',
 'Which of 28 academic search systems can support systematic, reproducible Boolean searching.', '28 search systems tested with a query-based method (precision, recall, reproducibility).',
 'Empirical query tests of Boolean operators, hit counts and reproducibility.', 'Only 14 of the 28 systems met all requirements; Google Scholar is judged inappropriate as a principal system.', 'Not studied beyond the abstract and summary paragraph.',
 ['only half of the search systems analyzed and only a few Open Access databases can be recommended for evidence syntheses without adding substantial caveats', 'Particularly, our findings demonstrate why Google Scholar is inappropriate as principal search system.', 'Overall, we found that only 14 of the 28 academic search systems examined are well-suited to evidence synthesis'],
 'Supports R1: the platform and database must be named because retrieval quality differs. Relevant to Saeedi and Ashraf (2024), who name Google Scholar as a main database.')

note('gusenbauer-2019-sizes', 'gusenbauer2019', 'Gusenbauer M (2019). Google Scholar to overshadow them all? Comparing the sizes of 12 academic search engines and bibliographic databases. Scientometrics 118:177-214.',
 'https://doi.org/10.1007/s11192-018-2958-5', 'opened in full (open access); abstract read only',
 'How large are 12 academic search engines and databases.', 'Query hit counts for 12 systems.', 'Iterative query optimisation to estimate maximum hits.', 'Estimates Google Scholar at 389 million records (abstract).', 'Not read beyond the abstract.',
 ['Google Scholar, with 389 million records, is currently the most comprehensive academic search engine.'],
 'The paper Sean\'s manuscript cites as "Gusenbauer 2022, Scientometrics 127(2), 1115-1139"; the real citation is 2019, 118:177-214. Do not cite it for the claim the manuscript makes without reading the relevant section.')

note('zupic-2015-methods', 'zupic2015', 'Zupic I, Cater T (2015). Bibliometric methods in management and organization. Organizational Research Methods 18(3):429-472 (I opened a repository copy whose layout differs from the journal).',
 'https://doi.org/10.1177/1094428114562629', 'opened in full (Goldsmiths repository copy); abstract and workflow headings read',
 'A reference for bibliometric methods and a five-step workflow for management scholars.', 'Citation and co-citation analysis of the journal Organizational Research Methods as a demonstration.', 'Workflow; appendix lists steps to reproduce the demonstration.',
 'Presents a five-step science-mapping workflow.', 'Not read beyond the abstract, introduction and workflow headings.',
 ['Science mapping is a combination of classification and visualization'],
 'Pre-dates the reporting guidelines; it argues bibliometrics make reviews "reproducible", which is what the audit tests. Its appendix shows what step-by-step reproduction looks like.')

note('ellegaard-2015-impact', 'ellegaard2015', 'Ellegaard O, Wallin JA (2015). The bibliometric analysis of scholarly production: how great is the impact? Scientometrics 105:1809-1831.',
 'https://doi.org/10.1007/s11192-015-1645-z', 'opened in full (open access); abstract read only',
 'Analyses the bibliometric literature itself (Web of Science).', 'Bibliometric articles extracted from Web of Science.', 'Citation and keyword analysis.', 'Abstract reports a shift in contributing countries and a self-perpetuating effect in citing.', 'Not read beyond the abstract.',
 ['A noticeable shift is observed in those countries which contribute to the pool of bibliometric analysis'],
 'Background only: shows bibliometric analysis is itself a studied literature. Low priority.')

note('koo-2023-priba', 'koo2023_priba', 'Koo M, Lin S-C (2023). An analysis of reporting practices in the top 100 cited health and medicine-related bibliometric studies from 2019 to 2021 based on a proposed guidelines. Heliyon 9(6):e16780.',
 'https://doi.org/10.1016/j.heliyon.2023.e16780', 'opened in full (Europe PMC PMC10245063; no page numbers)',
 'How completely do highly cited health and medicine bibliometric studies report, judged against a 25-item checklist (PRIBA) adapted from PRISMA 2020?',
 'Web of Science Core Collection records (9,476 for the keyword "bibliometric"; 2,681 after language and article-type limits); the 100 top-cited by normalised citations, 2019-2021, analysed with bibliometrix.',
 'Item-by-item coding of the 100 papers against PRIBA.',
 'All 100 gave a search strategy and keywords (item 7); 99 percent named the main data source (5a); 94 percent described indicators and software (items 8, 9); 62 percent stated the search date (5c); 75 percent stated inclusion and exclusion criteria (6); 60 percent described the search and selection results (10); 79 percent gave a funding statement and 28 percent a data availability statement (18); only 24 percent described the database itself (5b).',
 'Health and medicine only; COVID-19 papers over-represented in the period; PRIBA is a proposal without a consensus process (read from the limitations paragraph; I did not read all of it).',
 ['Specify the date when the search was conducted.', 'Specify the software package(s) used and the settings selected.', 'Specify if data are publicly available and the route of access.', 'only 62% of the articles explicitly indicated the date when the search was conducted (item 5c)'],
 'Nearest prior audit of this kind (health field, top-cited papers, binary items). Gives a baseline: the five green-fintech reviews I scored give a full search date in 1 of 5, software with settings in 2 of 5, and a data statement in 3 of 5 (statements only). Not a like-for-like comparison: different field, scoring scale and sample. Source for rubric R3, R8, R9, R10.')

note('stephen-2025-implicit-standards', 'arxiv2508_16276', 'Stephen D, Schniedermann A, Lovakov A, Schmidt M, Ottaviani M, Sorgatz N, Cruz Romero R, Moeller T, Aman V, Stahlschmidt S (2025). Implicit reporting standards in bibliometric research: what can reviewer comments tell us about reporting completeness? arXiv:2508.16276 (preprint, v1).',
 'https://arxiv.org/abs/2508.16276', 'opened in full (arXiv PDF, 23 pages; preprint, not peer reviewed)',
 'What do peer reviewers ask bibliometric authors to report, and how does that compare with the GLOBAL, PRIBA and BIBLIO guidelines?',
 '182 open peer reviews of 85 bibliometric studies (library and information science journals and conferences, and non-LIS journals); 968 reviewer comments.',
 'Inductive classification into 11 broad categories and 68 sub-categories; 49 derived recommendations compared item by item with three guidelines.',
 'Reviewers mostly ask for completeness and clarity of data, methods and results; the 49 recommendations covered 60-80 percent of the guideline items and the guidelines covered 45-65 percent of the recommendations (abstract).',
 'Open-peer-review sample only; three authors helped develop GLOBAL (declared in the paper); data in a shared spreadsheet, final version promised on Zenodo.',
 ["Our recommendations addressed 60-80% of the guidelines' items, while the guidelines covered 45-65% of our recommendations."],
 'Supports the claim that the rubric items are what reviewers ask for, without proving it (I did not map my ten items to its 49 recommendations). Mentions PRIBA, GLOBAL and BIBLIO together, which is how I found PRIBA and GLOBAL.')

bad = []
idx = ['# Reading notes: index', '', 'Notes are summaries of text I opened, with machine-checked verbatim quotations (40 words or fewer). "Skimmed" parts are marked inside each note. One further relevant paper, Farooq, Nasir and Khan (2023, Scientometrics 128:4855-4874, https://doi.org/10.1007/s11192-023-04765-8), is closed access with no abstract in Crossref or OpenAlex: metadata only, no note written.', '',
       '| File | Source | Access | One-line takeaway |', '|---|---|---|---|']
for n in N:
    pages = pages_of('../data/fulltext/' + n['text'] + '.txt'); allt = ' '.join(pages[p] for p in sorted(pages))
    ql = []
    for q in n['quotes']:
        nq = norm(q); hit = [p for p, tx in pages.items() if nq in tx]
        if not hit:
            if nq in allt: hit = ['page break']
            elif nq.replace(' ', '') in allt.replace(' ', ''): hit = ['pdf spacing']
            else: bad.append((n['fn'], q)); continue
        ql.append((q, ','.join(str(h) for h in hit)))
    md = [f"# {n['fn']}", '', f"**Citation:** {n['cite']}", f"**Link:** {n['link']}", f"**Access:** {n['access']}", '',
          f"**Research question:** {n['rq']}", '', f"**Data and sample:** {n['data']}", '', f"**Method and identification:** {n['method']}", '', f"**Main results (numbers):** {n['results']}", '',
          f"**Limitations stated by the authors:** {n['limits']}", '', '**Quotations** (page = PDF page index in the file opened; 0 = no page markers):']
    for q, pg in ql: md.append(f'- "{q}" (p. {pg})')
    md += ['', f"**How it bears on the audit:** {n['bears']}", '']
    open(OUT + n['fn'] + '.md', 'w', encoding='utf-8').write('\n'.join(md))
    idx.append(f"| {n['fn']}.md | {n['cite'][:70]}... | {n['access'].split(' (')[0]} | {n['bears'].split('. ')[0]}. |")
open(OUT + '00-index.md', 'w', encoding='utf-8').write('\n'.join(idx) + '\n')
if bad:
    for b in bad: print('QUOTE NOT FOUND', b)
    sys.exit(1)
print('notes written:', len(N))
