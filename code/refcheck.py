"""Check each reference in the 24 May 2026 manuscript against Crossref (query.bibliographic, top 5, best title match).
Output: results/repair/reference_check_crossref.csv. Judgement of 'resolves / does not resolve' is made by hand afterwards
(see results/repair/reference_verdicts.csv) because title similarity alone does not catch wrong volume/article numbers."""
import sys, os, csv, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netcache import get

REFS = [
 ('R1', 'Arner, D.W., Barberis, J.N. and Buckley, R.P. (2015) The Evolution of FinTech: A New Post-Crisis Paradigm? Georgetown Journal of International Law, 47, pp. 1271-1319', 'The Evolution of FinTech: A New Post-Crisis Paradigm?', 2015),
 ('R2', 'Ozili, P.K. (2022) Green finance research around the world: a review of literature. International Journal of Green Economics', 'Green finance research around the world: a review of literature', 2022),
 ('R3', 'Lee, I., & Shin, Y. J. (2018). Fintech: Ecosystem, business models, investment decisions, and challenges. Business horizons, 61(1), 35-46.', 'Fintech: Ecosystem, business models, investment decisions, and challenges', 2018),
 ('R4', 'Campiglio, E. (2016). Beyond carbon pricing: The role of banking and monetary policy in financing the transition to a low-carbon economy. Ecological economics, 121, 220-230.', 'Beyond carbon pricing: The role of banking and monetary policy in financing the transition to a low-carbon economy', 2016),
 ('R5', 'Zhou, Z., Chau, K. Y., Sibghatullah, A., Moslehpour, M., Tien, N. H., & Shukurullaevich, K. N. (2024). The role of green finance, environmental benefits, fintech development, and natural resource management in advancing sustainability. Resources Policy, 92, 105013.', 'The role of green finance, environmental benefits, fintech development, and natural resource management in advancing sustainability', 2024),
 ('R6', 'Liu, Y. (2025). Whether fintech, natural resources, green finance and environmental tax affect CO2 emissions in China? A step towards green initiatives. Energy, 320, 135181.', 'Whether fintech, natural resources, green finance and environmental tax affect CO2 emissions in China? A step towards green initiatives', 2025),
 ('R7', 'Jia, Z., Feng, T., & Jing, H. (2025). Digital finance and sustainable lending in rural china: The role of fintech in green credit expansion. Finance Research Letters, 108340.', 'Digital finance and sustainable lending in rural china: The role of fintech in green credit expansion', 2025),
 ('R8', 'Chien, F., Zhang, Y., & Sadiq, M. (2025). Fintech innovation in green finance: A disruptive force or a complementary tool?. International Review of Economics & Finance, 104658.', 'Fintech innovation in green finance: A disruptive force or a complementary tool?', 2025),
 ('R9', 'Al Doghan, M. A., & Chong, K. W. (2023). Fintech adoption and environmental sustainability: Mediating role of green finance, investment and innovation. International Journal of Operations and Quantitative Management, 29(2), 296-315.', 'Fintech adoption and environmental sustainability: Mediating role of green finance, investment and innovation', 2023),
 ('R10', 'Hemanand, D., Mishra, N., Premalatha, G., et al. (2022). Applications of intelligent model to analyze the green finance for environmental development in the context of artificial intelligence. Computational Intelligence and Neuroscience, 2022(1), 2977824.', 'Applications of intelligent model to analyze the green finance for environmental development in the context of artificial intelligence', 2022),
 ('R11', 'Zaid, M. A. K., Khan, M. F., et al. (2025). The future of green finance: How digital transformation and FinTech drive sustainability. Discover Sustainability, 6(1), 480.', 'The future of green finance: How digital transformation and FinTech drive sustainability', 2025),
 ('R12', 'Kwong, R., Kwok, M. L. J., & Wong, H. S. (2023). Green FinTech innovation as a future research direction: a bibliometric analysis on green finance and FinTech. Sustainability, 15(20), 14683.', 'Green FinTech innovation as a future research direction: a bibliometric analysis on green finance and FinTech', 2023),
 ('R13', 'Khan, S. A. R., Yu, Z., Sharif, A., & Golpira, H. (2022). Determinants of economic growth and environmental sustainability: A bibliometric analysis. Environmental Science and Pollution Research, 29(20), 29730-29745.', 'Determinants of economic growth and environmental sustainability: A bibliometric analysis', 2022),
 ('R14', 'Li, X., Du, J., & Long, H. (2023). Dynamic analysis of global green finance research: A bibliometric review. Journal of Cleaner Production, 382, 135245.', 'Dynamic analysis of global green finance research: A bibliometric review', 2023),
 ('R15', 'Xu, L., Chen, Y., & Zhao, X. (2024). Evolution and future trends of green finance research: A bibliometric analysis. Finance Research Letters, 59, 104563.', 'Evolution and future trends of green finance research: A bibliometric analysis', 2024),
 ('R16', 'Baas, J., Schotten, M., Plume, A., Cote, G., & Karimi, R. (2021). Scopus as a curated, high-quality bibliometric database for academic research. Quantitative Science Studies, 2(1), 377-386.', 'Scopus as a curated, high-quality bibliometric database for academic research', 2021),
 ('R17', 'Singh, V. K., Singh, P., & Karmakar, M. (2023). Application of bibliometric analysis in research evaluation: A review of methods and tools. Library Philosophy and Practice, 2023, 1-20.', 'Application of bibliometric analysis in research evaluation: A review of methods and tools', 2023),
 ('R18', 'Kwong, R., Kwok, M. L. J., & Wong, H. S. M. (2023). Green Fintech innovation as a future research direction: A bibliometric analysis on green finance and Fintech. Sustainability, 15(20), 14683. [second entry for the same paper]', 'Green Fintech innovation as a future research direction: A bibliometric analysis on green finance and Fintech', 2023),
 ('R19', 'Gusenbauer, M. (2022). Google Scholar to overshadow them all? Comparing the sizes of 12 academic search engines and bibliographic databases. Scientometrics, 127(2), 1115-1139.', 'Google Scholar to overshadow them all? Comparing the sizes of 12 academic search engines and bibliographic databases', 2022),
]
rows = []
for rid, full, title, year in REFS:
    s, r = get('https://api.crossref.org/works', params={'query.bibliographic': full, 'rows': 5,
               'select': 'DOI,title,author,issued,container-title,volume,issue,page,article-number'})
    items = r['message']['items'] if s == 200 else []
    best = None
    for it in items:
        t = (it.get('title') or [''])[0]
        sim = difflib.SequenceMatcher(None, title.lower(), t.lower()).ratio()
        if best is None or sim > best[0]:
            best = (sim, it)
    sim, it = best if best else (0, {})
    rows.append(dict(ref=rid, cited=full[:160], cited_year=year, best_title=(it.get('title') or [''])[0],
                     best_doi=it.get('DOI'), best_year=(it.get('issued', {}).get('date-parts') or [[None]])[0][0],
                     best_container=(it.get('container-title') or [''])[0], best_vol=it.get('volume'),
                     best_issue=it.get('issue'), best_page=it.get('page') or it.get('article-number'),
                     best_first_author=(it.get('author') or [{}])[0].get('family'), title_similarity=round(sim, 3)))
    print(rid, round(sim, 2), it.get('DOI'), rows[-1]['best_year'], rows[-1]['best_container'][:40], it.get('volume'),
          rows[-1]['best_page'], rows[-1]['best_first_author'], flush=True)
os.makedirs('../results/repair', exist_ok=True)
w = csv.DictWriter(open('../results/repair/reference_check_crossref.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
