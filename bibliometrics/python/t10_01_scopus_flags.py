"""Task 10, step 1: clean copy of the Scopus export and a transparent contamination rule.

Input : data/raw/scopus/fntech green finance.csv   (read-only copy of Sean's export; never edited)
Output: data/clean/scopus_168.csv                  (malformed row and empty trailing columns removed)
        data/clean/scopus_clean.csv                (contaminated records removed)
        tables/T01_scopus_record_flags.csv         (one row per record, every flag visible)
        tables/T01_contamination_summary.csv
Usage : python t10_01_scopus_flags.py

Rules (each is a column in the flags table):
  R0 keyword_only_match   the search terms (fintech AND "green finance") are NOT both present in title + abstract,
                          so the record entered the search through its keywords only.
  R1 inherited_kw_block   the record belongs to a source with >= 3 records in the export whose author-keyword
                          lists ALL contain the same block of >= 4 keywords that includes both search terms
                          (keywords attached at volume level, not chosen for the chapter).
  R2 no_topic_term_in_TA  title + abstract contain neither a fintech term nor a green/sustainable-finance term
                          (pattern TOPIC below).
  CONTAMINATED = R1 and R2.   R2 without R1 = "possibly off-topic, check by hand".
"""
import os
import re

import pandas as pd

from bm_common import BASE, CLEAN, RAW, TAB

SRC = os.path.join(RAW, "scopus", "fntech green finance.csv")
FT = re.compile(r"fin-?tech|financial technolog", re.I)
GF = re.compile(r"green financ", re.I)
TOPIC = re.compile(r"fin-?tech|financial technolog\w*|digital financ\w*|green (financ\w*|bank\w*|bonds?|credit|invest\w*|loans?)|"
                   r"sustainable financ\w*|climate financ\w*|carbon financ\w*", re.I)

raw = pd.read_csv(SRC, dtype=str, keep_default_na=False, encoding="utf-8-sig")
n_raw = len(raw)
keep_cols = [c for c in raw.columns if not c.startswith("Unnamed")]
bad = raw[~raw["Year"].str.fullmatch(r"\d{4}")]
d = raw[raw["Year"].str.fullmatch(r"\d{4}")][keep_cols].copy()
d.to_csv(os.path.join(CLEAN, "scopus_168.csv"), index=False, encoding="utf-8-sig")
bad[keep_cols].to_csv(os.path.join(CLEAN, "scopus_malformed_row.csv"), index=False, encoding="utf-8-sig")

ta = d["Title"] + " . " + d["Abstract"]
kw = d["Author Keywords"] + " ; " + d["Index Keywords"]
d["ft_in_TA"] = ta.map(lambda t: bool(FT.search(t)))
d["gf_in_TA"] = ta.map(lambda t: bool(GF.search(t)))
d["ft_in_keywords"] = kw.map(lambda t: bool(FT.search(t)))
d["gf_in_keywords"] = kw.map(lambda t: bool(GF.search(t)))
d["R0_keyword_only_match"] = ~(d.ft_in_TA & d.gf_in_TA)

# R1: inherited keyword block
d["_aks"] = d["Author Keywords"].map(lambda s: frozenset(k.strip().lower() for k in s.split(";") if k.strip()))
d["R1_inherited_kw_block"] = False
d["kw_block"] = ""
for src, g in d.groupby("Source title"):
    if len(g) < 3:
        continue
    common = frozenset.intersection(*g["_aks"])
    if len(common) >= 4 and any(FT.search(k) for k in common) and any(GF.search(k) for k in common):
        d.loc[g.index, "R1_inherited_kw_block"] = True
        d.loc[g.index, "kw_block"] = "; ".join(sorted(common))
d["R2_no_topic_term_in_TA"] = ta.map(lambda t: not TOPIC.search(t))
d["topic_terms_found_in_TA"] = ta.map(lambda t: "; ".join(sorted({m.group(0).lower() for m in TOPIC.finditer(t)})))
d["CONTAMINATED"] = d.R1_inherited_kw_block & d.R2_no_topic_term_in_TA
d["possibly_off_topic_check_by_hand"] = d.R2_no_topic_term_in_TA & ~d.R1_inherited_kw_block

cols = ["EID", "DOI", "Authors", "Title", "Year", "Source title", "Document Type", "Cited by", "Author Keywords", "ft_in_TA", "gf_in_TA",
        "ft_in_keywords", "gf_in_keywords", "R0_keyword_only_match", "R1_inherited_kw_block", "kw_block", "R2_no_topic_term_in_TA",
        "topic_terms_found_in_TA", "CONTAMINATED", "possibly_off_topic_check_by_hand"]
d[cols].sort_values(["CONTAMINATED", "R1_inherited_kw_block", "R0_keyword_only_match"], ascending=False).to_csv(
    os.path.join(TAB, "T01_scopus_record_flags.csv"), index=False, encoding="utf-8-sig")
clean = d[~d.CONTAMINATED][keep_cols]
clean.to_csv(os.path.join(CLEAN, "scopus_clean.csv"), index=False, encoding="utf-8-sig")

# effect on headline counts
def kwcount(frame, term):
    return int(frame["Author Keywords"].str.lower().str.split(";").map(lambda l: term in [k.strip() for k in l]).sum())


block_terms = sorted({k for b in d.kw_block[d.kw_block != ""] for k in b.split("; ")})
rows = [("rows in the raw export file", n_raw), ("malformed rows dropped (a reference fragment split across columns)", len(bad)),
        ("valid records", len(d)),
        ("R0: search terms only in keywords, not both in title+abstract", int(d.R0_keyword_only_match.sum())),
        ("R1: records in an inherited volume-level keyword block", int(d.R1_inherited_kw_block.sum())),
        ("R2: no fintech or green-finance term anywhere in title+abstract", int(d.R2_no_topic_term_in_TA.sum())),
        ("CONTAMINATED (R1 and R2)", int(d.CONTAMINATED.sum())),
        ("in the block but on-topic by R2 (kept)", int((d.R1_inherited_kw_block & ~d.R2_no_topic_term_in_TA).sum())),
        ("R2 outside the block (possibly off-topic, hand check)", int(d.possibly_off_topic_check_by_hand.sum())),
        ("cleaned corpus", len(clean)),
        ("share of the 168 that is contaminated (%)", round(100 * d.CONTAMINATED.sum() / len(d), 2))]
for t in block_terms:
    rows.append((f"author keyword '{t}': records before -> after cleaning", f"{kwcount(d, t)} -> {kwcount(d[~d.CONTAMINATED], t)}"))
fa = d["Authors"].str.split(";").str[0].str.strip()
top_fa = fa[d.R1_inherited_kw_block].value_counts()
if len(top_fa):
    name = top_fa.index[0]
    rows.append((f"records with '{name}' as an author: before -> after cleaning",
                 f"{int(d['Authors'].str.contains(re.escape(name)).sum())} -> {int(d[~d.CONTAMINATED]['Authors'].str.contains(re.escape(name)).sum())}"))
src_name = d[d.R1_inherited_kw_block]["Source title"].mode()
if len(src_name):
    s = src_name.iloc[0]
    rank_b = list(d["Source title"].value_counts().index).index(s) + 1
    vc_a = d[~d.CONTAMINATED]["Source title"].value_counts()
    rank_a = (list(vc_a.index).index(s) + 1) if s in vc_a.index else None
    rows.append((f"source '{s}': records (rank) before -> after", f"{int((d['Source title'] == s).sum())} (rank {rank_b}) -> {int(vc_a.get(s, 0))} (rank {rank_a})"))
pd.DataFrame(rows, columns=["item", "value"]).to_csv(os.path.join(TAB, "T01_contamination_summary.csv"), index=False, encoding="utf-8-sig")
for r in rows:
    print(r[0], "=", r[1])
print("\nCONTAMINATED titles:")
for t in d[d.CONTAMINATED]["Title"]:
    print(" -", t)
print("\nIn block but kept:")
for t in d[d.R1_inherited_kw_block & ~d.R2_no_topic_term_in_TA][["Title", "topic_terms_found_in_TA"]].values:
    print(" -", t[0], "|", t[1])
print("\nPossibly off-topic outside block:")
for t in d[d.possibly_off_topic_check_by_hand]["Title"]:
    print(" -", t)
