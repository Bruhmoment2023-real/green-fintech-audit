# Captions (depth/network/figures)

## N01_keyword_bursts.png
- Shows: Kleinberg burst intervals (two-state batch model, s=2, gamma=1) for OpenAlex keywords that occur in at least 8 of the 497 corpus records (125 keywords tested, 12 bursts found), top 15 by weight (all 12 shown).
- Data and settings: snapshot of the Phase-2 OpenAlex rebuild (`data/snapshot_master.csv`, pulled 2026-10-13 to 17), yearly batches 2021-2026 with 9, 10, 27, 74, 182 and 195 records; script `code/network_depth.py`. Counts by year for each keyword are in `keyword_bursts.csv`.
- Caution: six yearly batches, two of them with ten records or fewer, and a part-year 2026 make these bursts weak and unstable; OpenAlex keywords are algorithmic, not authors' words, and the corpus is dominated by 2025-26 records because the search was run in October 2026. Read it as a descriptive timeline, not a forecast.

## N02_main_path.png
- Shows: the global main path (red, 10 papers) and the other papers on key routes (blue, 18 key-route papers in all) of the direct-citation network among corpus papers, by search path count (SPC); x axis is publication year.
- Data and settings: 610 in-corpus citation links among 183 papers (3 weakly connected components; the main one has 179 papers and 608 links); links taken from OpenAlex reference lists, which exist for only 224 of the 497 records; same-year and backward-in-time links removed to make the graph acyclic; key routes start from the five highest-SPC links. Papers listed in `main_path_papers.csv` and `key_route_papers.csv`.
- Caution: OpenAlex reference lists are sparse (Phase-2 notes 1,533 references against 10,672 in Scopus), so the path reflects what OpenAlex records, and a paper outside the 497 cannot appear. The corpus starts in 2021, so earlier foundations of the field are absent. A main path shows the strongest chain of citations, not the most important papers.
