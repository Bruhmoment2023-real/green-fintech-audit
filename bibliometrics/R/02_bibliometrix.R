# Full Bibliometrix analysis set on one corpus.
# Usage: Rscript 02_bibliometrix.R [M.rds] [prefix] [keyword field: ID|DE] [corpus label] [cut years e.g. 2021,2024]
# Every figure is written to ../figures/<prefix>NN_name.png and every table to ../tables/<prefix>NN_name.csv.
.a <- commandArgs(FALSE); source(file.path(dirname(sub("^--file=", "", .a[grep("^--file=", .a)])), "common.R"))
arg <- commandArgs(TRUE)
MFILE  <- if (length(arg) >= 1) arg[1] else file.path(CLEAN, "M.rds")
PRE    <- if (length(arg) >= 2) arg[2] else "R"
KW     <- if (length(arg) >= 3) arg[3] else "ID"
LABEL  <- if (length(arg) >= 4) arg[4] else basename(BASE)
CUTS   <- if (length(arg) >= 5) as.numeric(strsplit(arg[5], ",")[[1]]) else c(2020, 2023)
if (!file.exists(MFILE)) MFILE <- file.path(CLEAN, MFILE)
M <- readRDS(MFILE)
N <- nrow(M); CUR <- 2026
KWNAME <- if (KW == "ID") (if (M$DB[1] == "SCOPUS") "Scopus index keywords" else "OpenAlex keywords") else "author keywords"
SRC <- sprintf("Corpus: %s (n = %d documents, %d-%d).", LABEL, N, min(M$PY, na.rm = TRUE), max(M$PY, na.rm = TRUE))
f <- function(n, name) sprintf("%s%02d_%s", PRE, n, name)
cat(SRC, "\n")
SMALL <- N < 50
if (SMALL) message("Corpus has fewer than 50 documents: network / thematic methods are skipped as not meaningful.")
remove_terms <- NULL
cfg <- tryCatch(fromJSON(file.path(BASE, "config.json")), error = function(e) list())
if (!is.null(cfg$remove_keywords)) remove_terms <- toupper(cfg$remove_keywords)
if (!is.null(remove_terms) && KW %in% names(M)) {
  M[[KW]] <- vapply(strsplit(ifelse(is.na(M[[KW]]), "", M[[KW]]), ";"), function(z) {
    z <- trimws(z); z <- z[!(z %in% remove_terms) & z != ""]; if (length(z)) paste(z, collapse = ";") else NA_character_ }, "")
}

# ---------------------------------------------------------------- 1 main information
res <- NULL; S <- NULL
safe("main information", {
  res <- biblioAnalysis(M, sep = ";")
  S <- summary(res, k = 25, pause = FALSE, verbose = FALSE)
  wtab(S$MainInformationDF, f(1, "main_information"))
})

# ---------------------------------------------------------------- 2 annual production + growth
safe("annual production", {
  ap <- as.data.frame(table(PY = M$PY)); ap$PY <- as.numeric(as.character(ap$PY))
  ap <- merge(data.frame(PY = min(ap$PY):max(ap$PY)), ap, all.x = TRUE); ap$Freq[is.na(ap$Freq)] <- 0
  ap$cum <- cumsum(ap$Freq)
  full <- ap[ap$PY < CUR, ]
  first_nz <- full$PY[which(full$Freq > 0)[1]]
  cagr <- if (nrow(full) > 1) ((tail(full$Freq, 1) / full$Freq[full$PY == first_nz])^(1 / (max(full$PY) - first_nz)) - 1) * 100 else NA
  last5 <- full[full$PY >= max(full$PY) - 5, ]
  cagr5 <- if (nrow(last5) > 1 && last5$Freq[1] > 0) ((tail(last5$Freq, 1) / last5$Freq[1])^(1 / (nrow(last5) - 1)) - 1) * 100 else NA
  ap$growth_pct <- c(NA, round(diff(ap$Freq) / pmax(head(ap$Freq, -1), 1) * 100, 1))
  wtab(ap, f(2, "annual_production"))
  wtab(data.frame(metric = c("bibliometrix annual growth rate % (first to last year, last year partial)",
                             sprintf("compound annual growth %% %d-%d (full years only)", first_nz, max(full$PY)),
                             sprintf("compound annual growth %% %d-%d", min(last5$PY), max(last5$PY))),
                  value = round(c(if (!is.null(S)) S$AnnualGrowthRate else NA, cagr, cagr5), 2)), f(2, "growth_rates"))
  p <- ggplot(ap, aes(PY, Freq)) + geom_col(aes(fill = PY == CUR), width = 0.8, show.legend = FALSE) +
    scale_fill_manual(values = c(`FALSE` = PAL[1], `TRUE` = "grey70")) +
    geom_text(aes(label = Freq), vjust = -0.4, size = 3) +
    scale_x_continuous(breaks = seq(min(ap$PY), max(ap$PY), by = ifelse(nrow(ap) > 14, 2, 1))) +
    labs(title = "Annual scientific production", subtitle = sprintf("%s  Compound annual growth %d-%d: %.1f%%; last five full years: %.1f%%", SRC, first_nz, max(full$PY), cagr, cagr5),
         x = "Publication year", y = "Documents in corpus", caption = sprintf("Grey bar = %d, incomplete year (search date in README).", CUR)) + theme_bm()
  gsave(p, f(2, "annual_production"), svg = TRUE)
  cap(f(2, "annual_production"), "Annual scientific production", "Number of corpus documents per publication year, with compound annual growth rates.",
      paste(SRC, "Counts of M$PY; growth from full years only. Table: tables/", f(2, "annual_production"), ".csv"),
      "Growth reflects what the search rules and the databases capture, and recent years are inflated by preprints that older years lack; it is not a clean measure of the field's true growth.")
})

# ---------------------------------------------------------------- 3 average citations per year
safe("average citations per year", {
  cy <- M |> as.data.frame() |> group_by(PY) |> summarise(N = n(), MeanTCperDoc = mean(TC), MedianTC = median(TC),
                                                          CitableYears = CUR - PY[1] + 1, .groups = "drop") |>
    mutate(MeanTCperYear = MeanTCperDoc / CitableYears)
  wtab(cy, f(3, "average_citations_per_year"))
  p <- ggplot(cy, aes(PY, MeanTCperYear)) + geom_line(colour = PAL[2], linewidth = 1) + geom_point(aes(size = N), colour = PAL[2]) +
    scale_size_continuous(name = "Documents that year", range = c(1.5, 6)) +
    labs(title = "Average citations per document per year, by publication year", subtitle = SRC,
         x = "Publication year", y = "Mean citations per document per citable year") + theme_bm()
  gsave(p, f(3, "average_citations_per_year"))
  cap(f(3, "average_citations_per_year"), "Average citations per year", "Mean total citations per document divided by years since publication, for each publication year.",
      paste(SRC, "Citations = database citation count at the pull date; citable years =", CUR, "- PY + 1."),
      "A few very highly cited papers drive the peaks; years with few documents are unstable (point size shows n).")
})

# ---------------------------------------------------------------- 4 sources + Bradford
safe("most relevant sources", {
  so <- as.data.frame(sort(table(M$SO), decreasing = TRUE)); names(so) <- c("Source", "Documents")
  so$Share_pct <- round(100 * so$Documents / N, 2)
  wtab(so, f(4, "sources"))
  top <- head(so, 20); top$Source <- factor(trunc_lab(as.character(top$Source), 60), levels = rev(trunc_lab(as.character(top$Source), 60)))
  p <- ggplot(top, aes(Documents, Source)) + geom_col(fill = PAL[1]) + geom_text(aes(label = Documents), hjust = -0.2, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
    labs(title = "Most relevant sources (top 20)", subtitle = SRC, x = "Documents in corpus", y = NULL) + theme_bm()
  gsave(p, f(4, "most_relevant_sources"), h = 7)
  cap(f(4, "most_relevant_sources"), "Most relevant sources", "The 20 venues (journals, conferences, preprint servers) with the most corpus documents.",
      paste(SRC, "Source = venue string as supplied by the database, upper-cased."),
      "Venue names are not fully harmonised (workshops and proceedings volumes can be split or merged), and a preprint server counts as one 'source'.")
})
safe("bradford", {
  b <- bradford(M)
  wtab(b$table, f(4, "bradford_zones"))
  bt <- b$table
  zc <- as.data.frame(table(Zone = bt$Zone)); zs <- tapply(bt$Freq, bt$Zone, sum)
  p <- ggplot(bt, aes(Rank, Freq)) + geom_area(data = bt[bt$Zone == "Zone 1", ], fill = "grey80") + geom_line(colour = PAL[1], linewidth = 1) +
    scale_x_log10() + labs(title = "Bradford's law: source scattering", subtitle = sprintf("%s  Core zone (shaded): %d sources hold %d documents; zone 2: %d sources; zone 3: %d sources.",
                                                                                         SRC, zc$Freq[1], zs[1], zc$Freq[2], zc$Freq[3]),
                           x = "Source rank (log scale)", y = "Documents per source") + theme_bm()
  gsave(p, f(4, "bradford_law"))
  cap(f(4, "bradford_law"), "Bradford's law", "Sources ranked by productivity; the shaded core zone holds about one third of all documents.",
      paste(SRC, "bibliometrix::bradford(); zones in tables/", f(4, "bradford_zones"), ".csv"),
      "Bradford zones describe concentration only; a 'core' source is the most frequent, not necessarily the best or the most relevant.")
})

# ---------------------------------------------------------------- 5 source dynamics
safe("source dynamics", {
  sg <- sourceGrowth(M, top = 8, cdf = TRUE)
  wtab(sg, f(5, "source_dynamics_cumulative"))
  lg <- pivot_longer(sg, -Year, names_to = "Source", values_to = "Cumulative")
  lg$Source <- trunc_lab(lg$Source, 45)
  p <- ggplot(lg, aes(Year, Cumulative, colour = Source)) + geom_line(linewidth = 1) + scale_colour_manual(values = PAL) +
    labs(title = "Source dynamics: cumulative documents in the eight most frequent sources", subtitle = SRC, x = "Publication year", y = "Cumulative documents") +
    theme_bm() + guides(colour = guide_legend(ncol = 2)) + theme(legend.text = element_text(size = 8))
  gsave(p, f(5, "source_dynamics"), h = 7.5)
  cap(f(5, "source_dynamics"), "Source dynamics", "Cumulative number of corpus documents over time in the eight most frequent sources.",
      paste(SRC, "bibliometrix::sourceGrowth(top = 8, cdf = TRUE)."),
      "A steep recent line for a preprint server partly reflects papers that have not yet appeared in their final venue.")
})

# ---------------------------------------------------------------- 6 authors
safe("authors", {
  au <- explode(M$AU)
  au$TC <- M$TC[au$row]; au$PY <- M$PY[au$row]
  au$LCS <- if ("LCS_EXACT" %in% names(M)) M$LCS_EXACT[au$row] else NA
  nau <- lengths(strsplit(ifelse(is.na(M$AU), "", M$AU), ";", fixed = TRUE)); au$frac <- 1 / pmax(nau[au$row], 1)
  at <- au |> group_by(Author = value) |> summarise(Documents = n(), Fractionalised = round(sum(frac), 2), TotalCitations = sum(TC),
                                                    LocalCitations = sum(LCS), FirstYear = min(PY), LastYear = max(PY), .groups = "drop") |> arrange(desc(Documents), desc(TotalCitations))
  # h-index within corpus
  hh <- au |> group_by(Author = value) |> summarise(h_index_in_corpus = { t <- sort(TC, decreasing = TRUE); sum(t >= seq_along(t)) }, .groups = "drop")
  at <- left_join(at, hh, by = "Author")
  wtab(at, f(6, "authors"))
  top <- head(at, 20); top$Author <- factor(top$Author, levels = rev(top$Author))
  p <- ggplot(top, aes(Documents, Author)) + geom_col(fill = PAL[1]) + geom_text(aes(label = Documents), hjust = -0.2, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
    labs(title = "Most productive authors (top 20)", subtitle = SRC, x = "Documents in corpus (full counting)", y = NULL) + theme_bm()
  gsave(p, f(6, "most_productive_authors"), h = 7)
  cap(f(6, "most_productive_authors"), "Most productive authors", "Authors with the most documents in the corpus (each co-author counted once per paper).",
      paste(SRC, "Author strings 'SURNAME INITIALS' built from database author names; table also gives fractional counts and citations."),
      "Authors are matched by surname and initials only, so different people with the same short name are merged and one person with name variants is split.")
  top2 <- at |> arrange(desc(TotalCitations)) |> head(20); top2$Author <- factor(top2$Author, levels = rev(top2$Author))
  p2 <- ggplot(top2, aes(TotalCitations, Author)) + geom_col(fill = PAL[2]) + geom_text(aes(label = TotalCitations), hjust = -0.15, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most cited authors (top 20, total citations to their corpus documents)", subtitle = SRC, x = "Total citations (global)", y = NULL) + theme_bm()
  gsave(p2, f(6, "most_cited_authors"), h = 7)
  cap(f(6, "most_cited_authors"), "Most cited authors", "Authors ranked by the summed global citation counts of their documents in the corpus.",
      paste(SRC, "Sum of database citation counts over each author's corpus papers; every co-author receives the full count."),
      "One heavily cited multi-author paper lifts all of its co-authors; this is not a measure of individual contribution.")
})
safe("lotka", {
  L <- lotka(M)
  ap <- L$AuthorProd; names(ap)[1:3] <- c("N.Articles", "N.Authors", "Freq")
  ap$Theoretical_beta2 <- 10^(log10(ap$Freq[1]) - 2 * log10(ap$N.Articles))
  wtab(ap, f(6, "lotka"))
  lg <- pivot_longer(ap[, c("N.Articles", "Freq", "Theoretical_beta2")], -N.Articles, names_to = "Series", values_to = "Share")
  lg$Series <- ifelse(lg$Series == "Freq", "Observed", "Lotka's law (exponent 2)")
  p <- ggplot(lg, aes(N.Articles, Share * 100, colour = Series, linetype = Series)) + geom_line(linewidth = 1) + geom_point() +
    scale_x_log10() + scale_y_log10() + scale_colour_manual(values = c(PAL[2], "grey40")) +
    labs(title = "Lotka's law: author productivity", subtitle = sprintf("%s  Estimated exponent beta = %.2f, C = %.2f, R2 = %.2f", SRC, L$Beta, L$C, L$R2),
         x = "Documents written (log scale)", y = "% of authors (log scale)") + theme_bm()
  gsave(p, f(6, "lotka_law"))
  cap(f(6, "lotka_law"), "Lotka's law", "Share of authors by number of corpus documents, against the inverse-square law.",
      paste(SRC, "bibliometrix::lotka(); table in tables/", f(6, "lotka"), ".csv"),
      "A good fit says only that most authors appear once; name ambiguity (see author caption) distorts the tail.")
})
safe("authors production over time", {
  ao <- authorProdOverTime(M, k = 15, graph = FALSE)
  wtab(ao$dfAU, f(6, "authors_production_over_time"))
  p <- ao$graph + labs(title = "Top 15 authors' production over time", subtitle = SRC, x = "Author", y = "Year") + theme(plot.background = element_rect(fill = "white", colour = NA))
  gsave(p, f(6, "authors_production_over_time"), h = 7)
  cap(f(6, "authors_production_over_time"), "Authors' production over time", "For the 15 most productive authors: bubble size = documents that year, colour intensity = citations per year.",
      paste(SRC, "bibliometrix::authorProdOverTime(k = 15)."),
      "Same name-matching caveat as the author ranking; a gap in a line may be a missing record, not inactivity.")
})

# ---------------------------------------------------------------- 7 affiliations and countries
cov_co <- mean(!is.na(M$AU_CO) & M$AU_CO != "")
COVTXT <- sprintf("Affiliation/country data exist for %.0f%% of documents (%d of %d).", 100 * cov_co, sum(!is.na(M$AU_CO) & M$AU_CO != ""), N)
safe("affiliations", {
  un <- explode(M$AU_UN) |> distinct(row, value) |> count(Affiliation = value, name = "Documents") |> arrange(desc(Documents))
  wtab(un, f(7, "affiliations"))
  top <- head(un, 20); top$Affiliation <- factor(trunc_lab(top$Affiliation, 60), levels = rev(trunc_lab(top$Affiliation, 60)))
  p <- ggplot(top, aes(Documents, Affiliation)) + geom_col(fill = PAL[3]) + geom_text(aes(label = Documents), hjust = -0.2, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
    labs(title = "Most relevant affiliations (top 20)", subtitle = paste(SRC, COVTXT), x = "Documents with at least one author from the institution", y = NULL) + theme_bm()
  gsave(p, f(7, "most_relevant_affiliations"), h = 7)
  cap(f(7, "most_relevant_affiliations"), "Most relevant affiliations", "Institutions appearing on the most corpus documents (once per document).",
      paste(SRC, COVTXT, "Institution names as disambiguated by the source database."),
      "Coverage is partial and uneven: preprints and workshop papers often carry no affiliation in the database, so institutions that publish mainly that way are under-counted.")
})
safe("countries", {
  co <- explode(M$AU_CO) |> distinct(row, value) |> count(Country = value, name = "Documents") |> arrange(desc(Documents))
  wtab(co, f(7, "countries_all_authors"))
  cc <- data.frame(row = seq_len(N), first = M$AU1_CO)
  allc <- explode(M$AU_CO) |> distinct(row, value) |> count(row, name = "ncountries")
  cc <- left_join(cc, allc, by = "row") |> filter(!is.na(first), first != "")
  ct <- cc |> group_by(Country = first) |> summarise(Articles = n(), SCP = sum(ncountries <= 1), MCP = sum(ncountries > 1), .groups = "drop") |>
    mutate(MCP_ratio = round(MCP / Articles, 3), Share_pct = round(100 * Articles / sum(Articles), 2)) |> arrange(desc(Articles))
  wtab(ct, f(7, "corresponding_author_countries"))
  top <- head(ct, 20); lg <- pivot_longer(top[, c("Country", "SCP", "MCP")], -Country, names_to = "Type", values_to = "n")
  lg$Country <- factor(lg$Country, levels = rev(top$Country))
  lg$Type <- factor(ifelse(lg$Type == "SCP", "Single-country publication", "Multi-country publication"), levels = c("Multi-country publication", "Single-country publication"))
  p <- ggplot(lg, aes(n, Country, fill = Type)) + geom_col() + scale_fill_manual(values = c(PAL[2], PAL[1]), name = NULL) +
    labs(title = "Corresponding-author countries (top 20)", subtitle = paste(SRC, COVTXT), x = "Documents", y = NULL,
         caption = "Corresponding author = author flagged as corresponding by the database, otherwise the first author.") + theme_bm()
  gsave(p, f(7, "corresponding_author_countries"), h = 7)
  cap(f(7, "corresponding_author_countries"), "Corresponding-author countries", "Documents by country of the corresponding (or first) author, split into single-country and multi-country papers.",
      paste(SRC, COVTXT, "Country from the institution country codes in the database."),
      "Only documents with affiliation data are counted, so shares are of the covered subset, not of the whole corpus.")
})
safe("country collaboration map", {
  if (sum(!is.na(M$AU_CO)) < 30) stop("too few documents with country data")
  Mc <- M[!is.na(M$AU_CO), ]
  nc <- biblioNetwork(Mc, analysis = "collaboration", network = "countries", sep = ";")
  mat <- as.matrix(nc); docs <- diag(mat); diag(mat) <- 0
  ed <- which(upper.tri(mat) & mat > 0, arr.ind = TRUE)
  edges <- data.frame(from = rownames(mat)[ed[, 1]], to = colnames(mat)[ed[, 2]], n = mat[ed]) |> arrange(desc(n))
  wtab(edges, f(7, "country_collaboration_links"))
  data(countries, package = "bibliometrix")
  xy <- countries[, c("countries", "Longitude", "Latitude")]
  edges <- edges |> left_join(xy, by = c("from" = "countries")) |> rename(x = Longitude, y = Latitude) |>
    left_join(xy, by = c("to" = "countries")) |> rename(xend = Longitude, yend = Latitude) |> filter(!is.na(x), !is.na(xend), !(x == xend & y == yend)) |> distinct(from, to, .keep_all = TRUE)
  w <- map_data("world"); w <- w[w$region != "Antarctica", ]
  fix <- c("USA" = "USA", "UNITED KINGDOM" = "UK", "KOREA" = "South Korea", "SOUTH KOREA" = "South Korea", "CZECH REPUBLIC" = "Czech Republic",
           "U ARAB EMIRATES" = "United Arab Emirates", "UNITED ARAB EMIRATES" = "United Arab Emirates")
  dd <- data.frame(country = names(docs), docs = as.numeric(docs))
  dd$region <- ifelse(dd$country %in% names(fix), fix[dd$country], tools::toTitleCase(tolower(dd$country)))
  w$docs <- dd$docs[match(tolower(w$region), tolower(dd$region))]
  thr <- if (nrow(edges) > 120) sort(edges$n, decreasing = TRUE)[120] else 1
  p <- ggplot() + geom_polygon(data = w, aes(long, lat, group = group, fill = docs), colour = "white", linewidth = 0.1) +
    scale_fill_gradient(low = "#cfe3f3", high = "#0b3c6d", na.value = "grey92", trans = "log10", name = "Documents (log scale)") +
    geom_curve(data = edges[edges$n >= thr, ], aes(x = x, y = y, xend = xend, yend = yend, linewidth = n), colour = PAL[2], alpha = 0.45, curvature = 0.2) +
    scale_linewidth_continuous(range = c(0.2, 2.2), name = "Co-authored documents") + coord_quickmap() +
    labs(title = "Country collaboration map", subtitle = paste(SRC, COVTXT), x = "Longitude", y = "Latitude",
         caption = sprintf("Links shown: country pairs with at least %d co-authored documents.", thr)) + theme_bm() + theme(panel.grid = element_blank())
  gsave(p, f(7, "country_collaboration_map"), w = 12, h = 7)
  cap(f(7, "country_collaboration_map"), "Country collaboration map", "Countries shaded by number of documents; red links join countries whose authors co-sign documents.",
      paste(SRC, COVTXT, "bibliometrix::biblioNetwork(collaboration, countries); links table in tables/."),
      "Countries with no affiliation data in the database appear empty even if they publish in this field; a link is co-authorship, not funding or influence.")
})

# ---------------------------------------------------------------- 8 most cited documents
LC <- NULL
safe("most global cited documents", {
  g <- data.frame(Document = M$SR, Title = M$TI, Year = M$PY, DOI = M$DI, TotalCitations = M$TC, TCperYear = round(M$TC / (CUR - M$PY + 1), 2)) |>
    arrange(desc(TotalCitations))
  wtab(head(g, 100), f(8, "most_global_cited_documents"))
  top <- head(g, 20); top$lab <- factor(trunc_lab(paste0(sub(",[^,]*$", "", top$Document), " - ", str_to_sentence(top$Title)), 85), levels = rev(trunc_lab(paste0(sub(",[^,]*$", "", top$Document), " - ", str_to_sentence(top$Title)), 85)))
  p <- ggplot(top, aes(TotalCitations, lab)) + geom_col(fill = PAL[2]) + geom_text(aes(label = TotalCitations), hjust = -0.15, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most globally cited documents (top 20)", subtitle = SRC, x = "Total citations in the database", y = NULL) + theme_bm(10)
  gsave(p, f(8, "most_global_cited_documents"), w = 13, h = 7)
  cap(f(8, "most_global_cited_documents"), "Most globally cited documents", "Corpus documents with the most citations from anywhere in the database.",
      paste(SRC, "Citation count as reported by the source database at the pull date."),
      "Global citations reward age and breadth: a general-purpose model or benchmark paper outranks a narrowly relevant study.")
})
safe("most local cited documents", {
  LC <- localCitations(M, sep = ";")
  lp <- LC$Papers
  ex <- data.frame(Paper = M$SR, Title = M$TI, LCS_exact_id_match = if ("LCS_EXACT" %in% names(M)) M$LCS_EXACT else NA)
  lp <- full_join(lp, ex, by = "Paper")
  lp$rank_field <- if (all(is.na(lp$LCS_exact_id_match))) lp$LCS else lp$LCS_exact_id_match
  lp <- lp |> arrange(desc(rank_field))
  wtab(head(lp, 150), f(8, "most_local_cited_documents"))
  if (!all(is.na(lp$LCS_exact_id_match))) {
    cc <- suppressWarnings(cor(lp$LCS, lp$LCS_exact_id_match, use = "complete.obs", method = "spearman"))
    wtab(data.frame(check = "Spearman correlation between bibliometrix string-matched LCS and exact identifier-matched LCS", value = round(cc, 3),
                    sum_bibliometrix = sum(lp$LCS, na.rm = TRUE), sum_exact = sum(lp$LCS_exact_id_match, na.rm = TRUE)), f(8, "local_citation_crosscheck"))
  }
  top <- head(lp, 20); labs_ <- trunc_lab(paste0(sub(",[^,]*$", "", top$Paper), " - ", str_to_sentence(top$Title)), 85)
  top$lab <- factor(labs_, levels = rev(labs_))
  p <- ggplot(top, aes(rank_field, lab)) + geom_col(fill = PAL[3]) + geom_text(aes(label = rank_field), hjust = -0.15, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most locally cited documents (top 20)", subtitle = SRC, x = "Citations received from other documents in this corpus", y = NULL) + theme_bm(10)
  gsave(p, f(8, "most_local_cited_documents"), w = 13, h = 7)
  cap(f(8, "most_local_cited_documents"), "Most locally cited documents", "Documents most cited by other documents inside the corpus - the field's own reference points.",
      paste(SRC, "Local citations counted by exact database identifiers where available (column LCS_exact_id_match); bibliometrix::localCitations() string matching is reported alongside as a cross-check."),
      "Local counts depend on reference lists being available: documents whose citing papers have no reference list in the database are under-counted.")
})
safe("most local cited references", {
  CRt <- citations(M, field = "article", sep = ";")
  cr <- data.frame(Reference = names(CRt$Cited), Citations = as.numeric(CRt$Cited))
  wtab(head(cr, 200), f(8, "most_cited_references"))
  top <- head(cr, 25); labs_ <- trunc_lab(sub(", DOI.*$", "", top$Reference), 80); top$lab <- factor(labs_, levels = rev(unique(labs_)))
  p <- ggplot(top, aes(Citations, lab)) + geom_col(fill = PAL[5]) + geom_text(aes(label = Citations), hjust = -0.15, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most cited references (top 25), whether or not they are in the corpus", subtitle = SRC, x = "Corpus documents citing the reference", y = NULL) + theme_bm(10)
  gsave(p, f(8, "most_cited_references"), w = 12, h = 7.5)
  cap(f(8, "most_cited_references"), "Most cited references", "The works the corpus cites most often, including works outside the corpus (the field's knowledge base).",
      paste(SRC, "bibliometrix::citations(field = 'article') over the reference strings."),
      "Method and tool papers (models, toolkits, metrics) dominate such lists because nearly everyone cites them; frequency is not topical closeness.")
})

# ---------------------------------------------------------------- 9 RPYS
safe("rpys", {
  r <- rpys(M, sep = ";", timespan = c(1950, CUR), graph = FALSE)
  wtab(r$rpysTable, f(9, "rpys_by_year"))
  crr <- r$CR |> arrange(desc(Freq)); wtab(head(crr, 300), f(9, "rpys_top_references"))
  rt <- r$rpysTable; names(rt)[1:3] <- c("Year", "Citations", "Deviation")
  peaks <- rt |> arrange(desc(Deviation)) |> head(6)
  p <- ggplot(rt, aes(Year)) + geom_line(aes(y = Citations, colour = "Cited references per year"), linewidth = 0.9) +
    geom_line(aes(y = Deviation, colour = "Deviation from 5-year median"), linewidth = 0.9) +
    geom_text_repel(data = peaks, aes(y = Deviation, label = Year), size = 3, colour = PAL[2]) +
    scale_colour_manual(values = c("grey25", PAL[2]), name = NULL) +
    labs(title = "Reference publication year spectroscopy (RPYS)", subtitle = SRC, x = "Publication year of the cited references", y = "Number of cited references") + theme_bm()
  gsave(p, f(9, "rpys"))
  cap(f(9, "rpys"), "Reference publication year spectroscopy", "How many cited references were published in each year, and where that count jumps above its 5-year median (labelled peaks = historical roots).",
      paste(SRC, "bibliometrix::rpys(timespan 1950-2026, centred median window)."),
      "In a fast field almost all references are from the last few years, so the curve mostly mirrors the field's own growth; only the early, isolated peaks point to roots.")
})

# ---------------------------------------------------------------- 10 keywords
kwt <- NULL
safe("keywords", {
  k <- explode(M[[KW]]) |> distinct(row, value) |> count(Keyword = value, name = "Documents") |> arrange(desc(Documents))
  kwt <- k; wtab(head(k, 300), f(10, "keywords"))
  covk <- mean(!is.na(M[[KW]]))
  top <- head(k, 30); top$Keyword <- factor(str_to_sentence(top$Keyword), levels = rev(str_to_sentence(top$Keyword)))
  p <- ggplot(top, aes(Documents, Keyword)) + geom_col(fill = PAL[6]) + geom_text(aes(label = Documents), hjust = -0.2, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
    labs(title = sprintf("Most frequent keywords (top 30; %s)", KWNAME), subtitle = sprintf("%s  Keywords exist for %.0f%% of documents.", SRC, 100 * covk), x = "Documents", y = NULL) + theme_bm()
  gsave(p, f(10, "most_frequent_keywords"), h = 8)
  cap(f(10, "most_frequent_keywords"), "Most frequent keywords", sprintf("The 30 most frequent %s.", KWNAME),
      paste(SRC, sprintf("Field %s; coverage %.0f%%.", KW, 100 * covk), if (KW == "ID" && M$DB[1] != "SCOPUS") "OpenAlex keywords are assigned by an algorithm from title and abstract, not chosen by the authors." else ""),
      "Keyword counts depend on who assigned them: algorithmic keywords are consistent but coarse, author keywords are precise but unstandardised.")
  pngdev(f(10, "wordcloud"), 9, 8); set.seed(42); par(mar = c(0, 0, 3, 0))
  kk <- head(k, 120)
  wordcloud::wordcloud(tolower(kk$Keyword), kk$Documents, scale = c(3.6, 0.5), random.order = FALSE, rot.per = 0.1, colors = PAL[c(1, 6, 3, 5, 2)])
  title(main = sprintf("Word cloud of the 120 most frequent %s", KWNAME), sub = SRC, cex.sub = 0.7)
  dev.off()
  cap(f(10, "wordcloud"), "Keyword word cloud", sprintf("The 120 most frequent %s; size proportional to document count.", KWNAME),
      paste(SRC, "wordcloud::wordcloud(), seed 42."), "A word cloud shows frequency only; position and colour carry no meaning, and long terms look bigger than short ones at equal counts.")
  tt <- head(k, 40); tt$lab <- paste0(str_to_sentence(tt$Keyword), "\n", tt$Documents)
  p <- ggplot(tt, aes(area = Documents, fill = Documents, label = lab)) + treemapify::geom_treemap(colour = "white") +
    treemapify::geom_treemap_text(colour = "white", place = "centre", reflow = TRUE, min.size = 5) +
    scale_fill_gradient(low = "#6ba3c9", high = "#0b3c6d", name = "Documents") +
    labs(title = sprintf("Treemap of the 40 most frequent %s", KWNAME), subtitle = SRC) + theme_bm()
  gsave(p, f(10, "keyword_treemap"), w = 11, h = 7)
  cap(f(10, "keyword_treemap"), "Keyword treemap", "Area of each tile = number of documents carrying the keyword (top 40).",
      paste(SRC, "treemapify::geom_treemap()."), "Documents carry several keywords, so areas overlap in meaning and do not sum to the corpus.")
})
safe("trend topics", {
  ty <- fieldByYear(M, field = KW, timespan = c(max(min(M$PY), 2012), CUR), min.freq = max(3, round(N / 300)), n.items = 4, graph = FALSE)
  wtab(ty$df_graph, f(10, "trend_topics"))
  p <- ty$graph + labs(title = sprintf("Trend topics (%s)", KWNAME), subtitle = SRC, x = "Keyword", y = "Year (line = first to third quartile of use; bubble = median year)") +
    theme(plot.background = element_rect(fill = "white", colour = NA))
  gsave(p, f(10, "trend_topics"), w = 10, h = 9)
  cap(f(10, "trend_topics"), "Trend topics", "For each year, the keywords whose median year of use falls there; bubble size = frequency, bar = interquartile range of years.",
      paste(SRC, "bibliometrix::fieldByYear(n.items = 4)."),
      "A term placed in a recent year is 'recent on average', not necessarily new: older steady terms can be hidden by the per-year cap of four items.")
})


# Draw a bibliometrix network (igraph object carrying size / colour / label attributes) with a cluster legend.
plot_net <- function(net, file, title, sub, w = 12, h = 10) {
  g <- net$graph
  pngdev(file, w, h); on.exit(dev.off())
  par(mar = c(2.5, 0.5, 3, 0.5))
  plot(g, layout = net$layout, main = title, cex.main = 1.25)
  cr <- net$cluster_res
  if (!is.null(cr) && nrow(cr) > 0) {
    cr <- cr[order(cr$cluster, -cr$pagerank_centrality), ]
    top <- cr[!duplicated(cr$cluster), ]
    cols <- V(g)$color[match(top$vertex, V(g)$name)]
    nn <- as.numeric(table(cr$cluster)[as.character(top$cluster)])
    legend("topleft", legend = sprintf("Cluster %s (%d nodes): %s", top$cluster, nn, trunc_lab(top$vertex, 38)), pt.bg = cols, pch = 21, col = "grey30",
           pt.cex = 1.6, cex = 0.72, bty = "n", title = "Clusters (named by their highest-PageRank node); node size = occurrences / degree")
  }
  mtext(sub, side = 1, line = 1, cex = 0.7)
}

if (!SMALL) {
# ---------------------------------------------------------------- 11 co-occurrence network
netname <- if (KW == "ID") "keywords" else "author_keywords"
safe("co-occurrence network", {
  nk <- biblioNetwork(M[!is.na(M[[KW]]), ], analysis = "co-occurrences", network = netname, sep = ";")
  net <- networkPlot(nk, normalize = "association", n = 60, Title = sprintf("Keyword co-occurrence network (top 60 %s; Louvain clusters)", KWNAME),
                     type = "fruchterman", size = 12, size.cex = TRUE, labelsize = 0.9, label.cex = TRUE, cluster = "louvain",
                     remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 4, edges.min = 2, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(11, "keyword_cooccurrence_network"), sprintf("Keyword co-occurrence network (top 60 %s; Louvain clusters)", KWNAME), SRC)
  wtab(net$cluster_res, f(11, "keyword_cooccurrence_clusters"))
  cap(f(11, "keyword_cooccurrence_network"), "Keyword co-occurrence network", "Keywords (nodes, sized by frequency) linked when they appear on the same document; colours are Louvain communities.",
      paste(SRC, "biblioNetwork(co-occurrences), association-strength normalisation, top 60 nodes, edges with at least 2 co-occurrences, Fruchterman-Reingold layout, seed 123."),
      "Clusters change with the number of nodes, the normalisation and the random seed; read them as a rough grouping, not a fixed taxonomy.")
})

# ---------------------------------------------------------------- 12 thematic map
safe("thematic map", {
  tm <- thematicMap(M, field = KW, n = 250, minfreq = 5, stemming = FALSE, size = 0.6, n.labels = 3, repel = TRUE, cluster = "louvain", seed = 1234)
  wtab(tm$clusters, f(12, "thematic_map_clusters")); wtab(tm$words, f(12, "thematic_map_words"))
  p <- tm$map + labs(title = sprintf("Thematic map (%s)", KWNAME), subtitle = paste(SRC, "Upper right = motor themes; upper left = niche; lower left = emerging or declining; lower right = basic."),
                     x = "Relevance degree (Callon centrality)", y = "Development degree (Callon density)") + theme(plot.background = element_rect(fill = "white", colour = NA))
  gsave(p, f(12, "thematic_map"), w = 11, h = 8)
  cap(f(12, "thematic_map"), "Thematic map", "Keyword clusters placed by centrality (links to other clusters) and density (internal cohesion): motor, niche, basic and emerging/declining themes.",
      paste(SRC, "bibliometrix::thematicMap(n = 250 keywords, minfreq = 5 per thousand documents, Louvain, seed 1234); cluster table in tables/."),
      "Quadrant positions are relative ranks within this corpus only; a cluster near an axis can switch quadrant with a small change in settings.")
})

# ---------------------------------------------------------------- 13 thematic evolution
safe("thematic evolution", {
  te <- thematicEvolution(M, field = KW, years = CUTS, n = 250, minFreq = 5, size = 0.6, n.labels = 2, repel = TRUE, cluster = "louvain", seed = 1234)
  wtab(te$Nodes, f(13, "thematic_evolution_nodes")); wtab(te$Edges, f(13, "thematic_evolution_edges"))
  w <- plotThematicEvolution(te$Nodes, te$Edges, measure = "inclusion", min.flow = 0.02)
  try(htmlwidgets::saveWidget(w, file.path(FIG, paste0(f(13, "thematic_evolution"), ".html")), selfcontained = FALSE, libdir = "html_lib",
                              title = "Thematic evolution"), silent = TRUE)
  nd <- as.data.frame(te$Nodes); ed <- as.data.frame(te$Edges)
  nd$idx <- nd$id
  nd$slice <- as.integer(as.character(nd$slice))
  nd <- nd |> group_by(slice) |> arrange(desc(freq), .by_group = TRUE) |> mutate(y = rev(seq_len(n())) / (n() + 1)) |> ungroup() |> as.data.frame()
  slab <- nd$group
  nd$lab <- nd$name
  e2 <- data.frame(from = ed$from, to = ed$to, w = ed$Inclusion)
  e2 <- e2 |> left_join(nd[, c("idx", "slice", "y")], by = c("from" = "idx")) |> rename(x1 = slice, y1 = y) |>
    left_join(nd[, c("idx", "slice", "y")], by = c("to" = "idx")) |> rename(x2 = slice, y2 = y) |> filter(w >= 0.02)
  periods <- tapply(slab, nd$slice, function(z) z[1])
  nd$nlab <- sprintf("%s (%d)", trunc_lab(nd$lab, 30), as.integer(nd$freq))
  p <- ggplot() + geom_segment(data = e2, aes(x = x1 + 0.12, y = y1, xend = x2 - 0.12, yend = y2, linewidth = w), colour = "grey55", alpha = 0.6) +
    geom_label(data = nd, aes(slice, y, label = nlab, fill = factor(slice)), size = 2.9, colour = "white", show.legend = FALSE, label.size = 0) +
    scale_fill_manual(values = PAL) + scale_linewidth_continuous(range = c(0.2, 3), name = "Inclusion index (share of shared keywords)") +
    scale_x_continuous(breaks = sort(unique(nd$slice)), labels = periods[as.character(sort(unique(nd$slice)))], expand = expansion(mult = 0.18)) +
    labs(title = sprintf("Thematic evolution across time slices (%s)", KWNAME), subtitle = paste(SRC, "Box = keyword cluster named by its most frequent keyword (number = keyword occurrences in the cluster)."), x = "Time slice", y = "Clusters ordered by size (largest at top)") + theme_bm() +
    theme(axis.text.y = element_blank(), panel.grid = element_blank())
  gsave(p, f(13, "thematic_evolution"), w = 13, h = 8)
  for (i in seq_along(te$TM)) {
    pm <- te$TM[[i]]$map + labs(title = sprintf("Thematic map, time slice %d (%s)", i, periods[i]), subtitle = SRC, x = "Relevance degree (Callon centrality)", y = "Development degree (Callon density)") +
      theme(plot.background = element_rect(fill = "white", colour = NA))
    gsave(pm, f(13, sprintf("thematic_map_slice%d", i)), w = 10, h = 7.5)
  }
  cap(f(13, "thematic_evolution"), "Thematic evolution", "Keyword clusters in each time slice and how they flow into clusters of the next slice (line width = share of shared keywords). Interactive version: same name .html; per-slice thematic maps: thematic_map_sliceN.png.",
      paste(SRC, sprintf("bibliometrix::thematicEvolution(cut years %s, n = 250, minFreq = 5, Louvain, seed 1234).", paste(CUTS, collapse = ", "))),
      "Cut years are a choice; early slices hold few documents, so their themes rest on small numbers and the flows from them are fragile.")
})

# ---------------------------------------------------------------- 14 co-citation
Mf <- M
safe("filter references", {
  l <- strsplit(ifelse(is.na(M$CR), "", M$CR), ";", fixed = TRUE)
  tb <- table(unlist(l)); keep <- names(tb)[tb >= 2]
  Mf$CR <- vapply(l, function(z) { z <- z[z %in% keep]; if (length(z)) paste(z, collapse = ";") else NA_character_ }, "")
  message(sprintf("references: %d unique, %d cited at least twice", length(tb), length(keep)))
})
safe("co-citation references", {
  ncc <- biblioNetwork(Mf[!is.na(Mf$CR), ], analysis = "co-citation", network = "references", sep = ";")
  net <- networkPlot(ncc, n = 60, Title = "Co-citation network of cited references (top 60; Louvain clusters)", type = "fruchterman", size = 10, size.cex = TRUE,
                     labelsize = 0.75, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 3, edges.min = 3, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(14, "cocitation_references_network"), "Co-citation network of cited references (top 60; Louvain clusters)", SRC)
  wtab(net$cluster_res, f(14, "cocitation_references_clusters"))
  cap(f(14, "cocitation_references_network"), "Co-citation network of references", "Cited works (nodes) linked when corpus documents cite them together; clusters approximate the intellectual bases of the field.",
      paste(SRC, "biblioNetwork(co-citation, references) on references cited at least twice; top 60 nodes, edges with at least 3 co-citations, Louvain, Fruchterman-Reingold."),
      "Only documents with a reference list in the database contribute, and reference strings are matched by first author, year and source, so variants of one work can appear as two nodes.")
})
safe("co-citation sources", {
  Ms <- metaTagExtraction(Mf[!is.na(Mf$CR), ], Field = "CR_SO", sep = ";")
  ncs <- biblioNetwork(Ms, analysis = "co-citation", network = "sources", sep = ";")
  net <- networkPlot(ncs, n = 40, Title = "Co-citation network of cited sources (top 40; Louvain clusters)", type = "fruchterman", size = 10, size.cex = TRUE,
                     labelsize = 0.75, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 3, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(14, "cocitation_sources_network"), "Co-citation network of cited sources (top 40; Louvain clusters)", SRC)
  wtab(net$cluster_res, f(14, "cocitation_sources_clusters"))
  cap(f(14, "cocitation_sources_network"), "Co-citation network of sources", "Venues (nodes) linked when works published in them are cited together by corpus documents.",
      paste(SRC, "metaTagExtraction(CR_SO) then biblioNetwork(co-citation, sources); top 40 nodes."),
      "Source names come from cited-reference strings and are unharmonised; 'ARXIV' is a single huge node that pulls everything towards it.")
})

# ---------------------------------------------------------------- 15 bibliographic coupling
safe("bibliographic coupling", {
  nbc <- biblioNetwork(Mf[!is.na(Mf$CR), ], analysis = "coupling", network = "references", sep = ";")
  net <- networkPlot(nbc, normalize = "salton", n = 60, Title = "Bibliographic coupling of documents (60 most connected; Louvain clusters)", type = "fruchterman", size = 8, size.cex = TRUE,
                     labelsize = 0.7, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 3, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(15, "bibliographic_coupling_network"), "Bibliographic coupling of documents (60 most connected; Louvain clusters)", SRC)
  wtab(net$cluster_res, f(15, "bibliographic_coupling_clusters"))
  cap(f(15, "bibliographic_coupling_network"), "Bibliographic coupling", "Corpus documents linked when their reference lists overlap; clusters are current research fronts.",
      paste(SRC, "biblioNetwork(coupling, references), Salton normalisation, top 60 nodes, Louvain."),
      "Coupling favours documents with long reference lists (surveys) and ignores documents whose references are missing from the database.")
})

# ---------------------------------------------------------------- 16 historiograph
safe("historiograph", {
  mc <- as.numeric(quantile(M$TC, 0.75, na.rm = TRUE))
  h <- histNetwork(M, min.citations = max(1, mc), sep = ";", verbose = FALSE)
  hp <- histPlot(h, n = 25, size = 4, labelsize = 3, verbose = FALSE)
  hd <- h$histData; wtab(hd[order(-hd$LCS), ][1:min(100, nrow(hd)), ], f(16, "historiograph_documents"))
  p <- hp$g + labs(title = "Historiograph: direct citation network of the 25 most locally cited documents", subtitle = SRC) + theme(plot.background = element_rect(fill = "white", colour = NA))
  gsave(p, f(16, "historiograph"), w = 13, h = 8)
  cap(f(16, "historiograph"), "Historiograph (direct citation network)", "The 25 most locally cited documents arranged by year, with arrows for direct citations between them.",
      paste(SRC, sprintf("bibliometrix::histNetwork(min.citations = %s) and histPlot(n = 25).", max(1, mc))),
      "The picture keeps only 25 nodes; an absent arrow can mean a missing reference list rather than no intellectual link.")
})

# ---------------------------------------------------------------- 17 collaboration networks
safe("collaboration authors", {
  na_ <- biblioNetwork(M[!is.na(M$AU), ], analysis = "collaboration", network = "authors", sep = ";")
  net <- networkPlot(na_, n = 60, Title = "Author collaboration network (60 most productive authors; Louvain clusters)", type = "fruchterman", size = 8, size.cex = TRUE,
                     labelsize = 0.75, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 3, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(17, "collaboration_network_authors"), "Author collaboration network (60 most productive authors; Louvain clusters)", SRC)
  wtab(net$cluster_res, f(17, "collaboration_authors_clusters"))
  cap(f(17, "collaboration_network_authors"), "Author collaboration network", "Authors linked by co-authorship; clusters are research groups.",
      paste(SRC, "biblioNetwork(collaboration, authors); top 60 authors; isolates removed."),
      "Short author names merge namesakes, which can create false bridges between groups.")
})
safe("collaboration institutions", {
  if (sum(!is.na(M$AU_UN)) < 50) stop("too few documents with institution data (under 50) - not meaningful")
  ni <- biblioNetwork(M[!is.na(M$AU_UN), ], analysis = "collaboration", network = "universities", sep = ";")
  net <- networkPlot(ni, n = 50, Title = "Institution collaboration network (top 50; Louvain clusters)", type = "fruchterman", size = 8, size.cex = TRUE,
                     labelsize = 0.7, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 3, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(17, "collaboration_network_institutions"), "Institution collaboration network (top 50; Louvain clusters)", paste(SRC, COVTXT))
  wtab(net$cluster_res, f(17, "collaboration_institutions_clusters"))
  cap(f(17, "collaboration_network_institutions"), "Institution collaboration network", "Institutions linked when their authors co-sign documents.",
      paste(SRC, COVTXT, "biblioNetwork(collaboration, universities); top 50."),
      "Built only from the documents that carry affiliations in the database (see coverage); absent institutions are not necessarily inactive.")
})
safe("collaboration countries", {
  if (sum(!is.na(M$AU_CO)) < 50) stop("too few documents with country data (under 50) - not meaningful")
  nc <- biblioNetwork(M[!is.na(M$AU_CO), ], analysis = "collaboration", network = "countries", sep = ";")
  net <- networkPlot(nc, n = 35, Title = "Country collaboration network (top 35; Louvain clusters)", type = "circle", size = 10, size.cex = TRUE,
                     labelsize = 0.9, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 4, alpha = 0.6, verbose = FALSE)
  plot_net(net, f(17, "collaboration_network_countries"), "Country collaboration network (top 35; Louvain clusters)", paste(SRC, COVTXT))
  wtab(net$cluster_res, f(17, "collaboration_countries_clusters"))
  cap(f(17, "collaboration_network_countries"), "Country collaboration network", "Countries linked by internationally co-authored documents.",
      paste(SRC, COVTXT, "biblioNetwork(collaboration, countries); top 35; circle layout."),
      "Same coverage limit as the country map; large countries sit in the centre because they publish more, not because they 'lead'.")
})

# ---------------------------------------------------------------- 18 three-field plot
safe("three-field plot", {
  left <- if (cov_co >= 0.4) "AU_CO" else "AU"
  tf <- threeFieldsPlot(M, fields = c(left, KW, "SO"), n = c(12, 15, 12))
  htmlwidgets::saveWidget(tf, file.path(FIG, paste0(f(18, "three_field_plot"), ".html")), selfcontained = FALSE, libdir = "html_lib", title = "Three-field plot")
  cap(paste0(f(18, "three_field_plot"), ".html"), "Three-field plot (interactive HTML)", sprintf("Sankey diagram linking %s (left), keywords (middle) and sources (right).", ifelse(left == "AU_CO", "author countries", "authors")),
      paste(SRC, "bibliometrix::threeFieldsPlot(n = 12, 15, 12). Saved as HTML because the plotly widget cannot be rendered to PNG without a browser."),
      "Only the top items of each field are shown, so flows describe the most frequent combinations, not the whole corpus.")
})
} # end !SMALL

save_caps(PRE)
cat("done. failures:", length(FAILS), "\n"); if (length(FAILS)) print(FAILS)
