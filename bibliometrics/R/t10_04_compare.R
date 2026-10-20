# Task 10, step 4: paired figures and the difference table - Scopus raw vs Scopus cleaned vs OpenAlex.
# Usage: Rscript t10_04_compare.R      (after 02_bibliometrix.R has been run with prefixes SR, SC and OA)
.a <- commandArgs(FALSE); source(file.path(dirname(sub("^--file=", "", .a[grep("^--file=", .a)])), "common.R"))
CORP <- c(SR = "Scopus raw (168)", SC = "Scopus cleaned (155)", OA = "OpenAlex rebuild")
nOA <- nrow(readRDS(file.path(CLEAN, "M.rds"))); CORP["OA"] <- sprintf("OpenAlex rebuild (%d)", nOA)
rd <- function(pre, name) { p <- file.path(TAB, paste0(pre, name, ".csv")); if (file.exists(p)) read.csv(p, check.names = FALSE, encoding = "UTF-8") else NULL }
norm_src <- function(x) { x <- toupper(x); x <- gsub("\\s*\\([^)]*\\)", "", x); x <- gsub("&", "AND", x); x <- gsub("^THE ", "", x); x <- gsub("[^A-Z0-9 ]", " ", x); trimws(gsub("\\s+", " ", x)) }
norm_kw <- function(x) { x <- tolower(x); x <- gsub("[^a-z0-9 ]", " ", x); trimws(gsub("\\s+", " ", x)) }

dims <- list(
  sources   = list(file = "04_sources", key = "Source", val = "Documents", norm = norm_src, title = "Top 10 sources", n = 10),
  keywords  = list(file = "10_keywords", key = "Keyword", val = "Documents", norm = norm_kw, title = "Top 15 keywords (Scopus: author keywords; OpenAlex: algorithmic keywords)", n = 15),
  countries = list(file = "07_countries_all_authors", key = "Country", val = "Documents", norm = toupper, title = "Top 10 countries (documents with at least one author from the country)", n = 10),
  corresponding_countries = list(file = "07_corresponding_author_countries", key = "Country", val = "Articles", norm = toupper, title = "Top 10 corresponding-author countries", n = 10),
  authors   = list(file = "06_authors", key = "Author", val = "Documents", norm = toupper, title = "Top 10 authors by documents", n = 10))

DIFF <- list(); SUMM <- list()
for (dn in names(dims)) {
  d <- dims[[dn]]
  L <- lapply(names(CORP), function(p) { t <- rd(p, d$file); if (is.null(t)) return(NULL)
    t <- data.frame(item = d$norm(t[[d$key]]), n = t[[d$val]]); t <- aggregate(n ~ item, t, sum); t <- t[order(-t$n, t$item), ]
    t$rank <- rank(-t$n, ties.method = "min"); t$corpus <- p; t$share <- round(100 * t$n / sum(t$n), 2); t })
  names(L) <- names(CORP); L <- L[!vapply(L, is.null, TRUE)]
  if (length(L) < 2) next
  tops <- lapply(L, function(t) head(t$item, d$n))
  uni <- unique(unlist(tops))
  wide <- data.frame(dimension = dn, item = uni)
  for (p in names(L)) { mt <- L[[p]][match(uni, L[[p]]$item), ]; wide[[paste0(p, "_rank")]] <- mt$rank; wide[[paste0(p, "_n")]] <- mt$n }
  if (all(c("SR", "SC") %in% names(L))) wide$rank_change_cleaning <- wide$SR_rank - wide$SC_rank
  if (all(c("SC", "OA") %in% names(L))) wide$rank_change_database <- wide$SC_rank - wide$OA_rank
  DIFF[[dn]] <- wide[order(wide[[paste0(names(L)[min(2, length(L))], "_rank")]]), ]
  prs <- combn(names(L), 2, simplify = FALSE)
  for (pr in prs) {
    a <- L[[pr[1]]]; b <- L[[pr[2]]]; ta <- head(a$item, d$n); tb <- head(b$item, d$n)
    cm <- merge(a[, c("item", "n")], b[, c("item", "n")], by = "item")
    rho <- if (nrow(cm) >= 5) suppressWarnings(cor(cm$n.x, cm$n.y, method = "spearman")) else NA
    SUMM[[length(SUMM) + 1]] <- data.frame(dimension = dn, pair = paste(pr, collapse = " vs "), top_n = d$n, shared_in_top_n = length(intersect(ta, tb)),
                                           jaccard_top_n = round(length(intersect(ta, tb)) / length(union(ta, tb)), 3), same_number_one = ta[1] == tb[1],
                                           items_in_both_corpora = nrow(cm), spearman_rho_on_shared_items = round(rho, 3))
  }
  # paired figure
  pl <- do.call(rbind, lapply(names(L), function(p) { t <- head(L[[p]], d$n); t$corpus_lab <- CORP[p]; t }))
  ref <- if ("SC" %in% names(tops)) tops$SC else tops[[1]]
  pl$status <- ifelse(pl$item %in% ref, "Also in the cleaned-Scopus top list", "Not in the cleaned-Scopus top list")
  pl$corpus_lab <- factor(pl$corpus_lab, levels = CORP[names(L)])
  pl$lab <- trunc_lab(if (dn == "keywords") pl$item else str_to_title(pl$item), 34)
  pl$ord <- paste(pl$corpus, sprintf("%03d", ave(-pl$n, pl$corpus, FUN = function(z) rank(z, ties.method = "first"))))
  p <- ggplot(pl, aes(n, reorder(ord, -as.numeric(factor(ord))), fill = status)) + geom_col() +
    geom_text(aes(label = n), hjust = -0.15, size = 2.8) +
    scale_y_discrete(labels = setNames(pl$lab, pl$ord)) + scale_x_continuous(expand = expansion(mult = c(0, 0.15))) +
    scale_fill_manual(values = c("Also in the cleaned-Scopus top list" = PAL[1], "Not in the cleaned-Scopus top list" = PAL[2]), name = NULL) +
    facet_wrap(~corpus_lab, scales = "free", nrow = 1) +
    labs(title = paste0(d$title, ": effect of cleaning and of database choice"),
         subtitle = "Same search (fintech AND \"green finance\", 2021-2026, articles and reviews). Left to middle = effect of removing 13 contaminated records; middle to right = effect of the database.",
         x = "Documents", y = NULL) + theme_bm(10) + theme(strip.text = element_text(face = "bold"))
  gsave(p, sprintf("C%02d_paired_%s", match(dn, names(dims)), dn), w = 15, h = if (d$n > 10) 7 else 5.8, svg = TRUE)
  cap(sprintf("C%02d_paired_%s", match(dn, names(dims)), dn), paste("Paired figure:", d$title),
      "The same ranking computed on the raw Scopus export, the cleaned Scopus export and the OpenAlex rebuild; red bars are items that are not in the cleaned-Scopus top list.",
      "Tables produced by 02_bibliometrix.R (prefixes SR, SC, OA); names normalised (upper case, bracketed qualifiers removed) before matching. Full numbers in tables/C_difference_table.csv.",
      if (dn == "keywords") "Scopus author keywords and OpenAlex algorithmic keywords are different kinds of object; a low overlap here is a property of the databases, not evidence that the literature differs."
      else "The OpenAlex corpus is larger and pulled seven months later, so some differences are time, not database; see database-comparison.md for the date-aligned counts.")
}
diff_all <- bind_rows(DIFF); wtab(diff_all, "C_difference_table")
summ <- bind_rows(SUMM); wtab(summ, "C_difference_summary")

# main information side by side
mi <- lapply(names(CORP), function(p) { t <- rd(p, "01_main_information"); if (is.null(t)) return(NULL); names(t) <- c("Description", CORP[p]); t[t$Description != "", ] })
mi <- mi[!vapply(mi, is.null, TRUE)]
MI <- Reduce(function(a, b) merge(a, b, by = "Description", all = TRUE, sort = FALSE), mi)
wtab(MI, "C_main_information_side_by_side")

# thematic maps: clusters and quadrants per corpus, plus a stitched picture
quad <- function(rc, rd_) ifelse(rc >= median(rc) & rd_ >= median(rd_), "motor", ifelse(rc < median(rc) & rd_ >= median(rd_), "niche",
                          ifelse(rc >= median(rc) & rd_ < median(rd_), "basic", "emerging or declining")))
tmc <- bind_rows(lapply(names(CORP), function(p) { t <- rd(p, "12_thematic_map_clusters"); if (is.null(t)) return(NULL)
  data.frame(corpus = CORP[p], cluster = t$name, keyword_occurrences = t$freq, callon_centrality = round(t$centrality, 3), callon_density = round(t$density, 2),
             quadrant = quad(t$rcentrality, t$rdensity), top_words = gsub("\n", "; ", t$words)) }))
wtab(tmc, "C_thematic_map_clusters_by_corpus")
files <- file.path(FIG, paste0(names(CORP), "12_thematic_map.png")); files <- files[file.exists(files)]
if (length(files) >= 2) {
  imgs <- lapply(files, png::readPNG)
  png(file.path(FIG, "C06_paired_thematic_maps.png"), width = 7 * length(imgs), height = 5.6, units = "in", res = 220, bg = "white")
  grid::grid.newpage()
  grid::pushViewport(grid::viewport(layout = grid::grid.layout(2, length(imgs), heights = grid::unit(c(0.07, 0.93), "npc"))))
  for (i in seq_along(imgs)) {
    grid::grid.text(CORP[sub("12_thematic_map.png", "", basename(files[i]))], vp = grid::viewport(layout.pos.row = 1, layout.pos.col = i), gp = grid::gpar(fontface = "bold", fontsize = 15))
    grid::grid.raster(imgs[[i]], vp = grid::viewport(layout.pos.row = 2, layout.pos.col = i))
  }
  dev.off()
  cap("C06_paired_thematic_maps", "Paired thematic maps", "The thematic map (Callon centrality by density) for each corpus, side by side.",
      "Stitched from SR12/SC12/OA12_thematic_map.png (bibliometrix::thematicMap, n = 250, minfreq = 5 per thousand, Louvain, seed 1234). Scopus maps use author keywords, the OpenAlex map uses OpenAlex keywords. Cluster table: tables/C_thematic_map_clusters_by_corpus.csv.",
      "Quadrants are relative ranks inside each corpus, and the keyword vocabularies differ between databases, so compare which topics cluster together, not exact positions.")
}

# year and source-type distributions, paired
yr <- bind_rows(lapply(names(CORP), function(p) { t <- rd(p, "02_annual_production"); if (is.null(t)) return(NULL); data.frame(corpus = CORP[p], PY = t$PY, n = t$Freq) }))
yr$corpus <- factor(yr$corpus, levels = CORP)
p <- ggplot(yr, aes(factor(PY), n, fill = corpus)) + geom_col(position = position_dodge(0.85), width = 0.8) +
  geom_text(aes(label = n), position = position_dodge(0.85), vjust = -0.4, size = 2.8) + scale_fill_manual(values = PAL[c(4, 1, 2)], name = NULL) +
  labs(title = "Documents per publication year in each corpus", subtitle = "Scopus export dated 22 March 2026; OpenAlex rebuild pulled 13 October 2026, so 2025-2026 are not like-for-like.",
       x = "Publication year", y = "Documents") + theme_bm()
gsave(p, "C07_paired_year_distribution", w = 10, h = 6, svg = TRUE)
cap("C07_paired_year_distribution", "Year distribution by corpus", "Annual document counts in the raw Scopus export, the cleaned export and the OpenAlex rebuild.",
    "tables/SR02, SC02, OA02_annual_production.csv.", "The two databases were queried seven months apart; the gap in 2025-2026 mixes later indexing with broader coverage.")
save_caps("C")
print(summ)
