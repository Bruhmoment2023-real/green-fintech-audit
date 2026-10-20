# Build the bibliometrix data frame (M) directly from data/clean/master.csv + references.csv.
# Usage: Rscript 01_build_M.R
# The frame uses Web-of-Science-style tags (DB = "ISI") so every bibliometrix function runs on its
# best-tested code path. Cited references are written as "FIRST AUTHOR, YEAR, SOURCE, DOI x".
.a <- commandArgs(FALSE); source(file.path(dirname(sub("^--file=", "", .a[grep("^--file=", .a)])), "common.R"))

m    <- fread(file.path(CLEAN, "master.csv"), encoding = "UTF-8", na.strings = NULL, quote = "\"")
refs <- fread(file.path(CLEAN, "references.csv"), encoding = "UTF-8", na.strings = NULL, quote = "\"")
m <- as.data.frame(m); refs <- as.data.frame(refs)
cat("master rows:", nrow(m), " reference links:", nrow(refs), "\n")

refs <- refs[refs$cr != "", ]
cr <- refs |> group_by(citing) |> summarise(CR = paste(unique(cr), collapse = ";"), .groups = "drop")
m <- left_join(m, cr, by = c("id" = "citing"))

data(countries, package = "bibliometrix")
iso <- setNames(countries$countries, countries$iso2)
pair2c1 <- function(x) {            # "Inst A [IN]; Inst B [US]" -> "INST A, INDIA;INST B, USA"
  if (is.na(x) || x == "") return(NA_character_)
  p <- trimws(strsplit(x, "; ", fixed = TRUE)[[1]])
  nm <- toupper(gsub(",", " ", sub(" \\[[A-Z]*\\]$", "", p)))
  cc <- sub("^.*\\[([A-Z]*)\\]$", "\\1", p)
  cn <- ifelse(cc %in% names(iso), iso[cc], "")
  paste(ifelse(cn == "", nm, paste0(nm, ", ", cn)), collapse = ";")
}
codes2names <- function(x, uniq = FALSE) {
  if (is.na(x) || x == "") return(NA_character_)
  cc <- strsplit(x, ";", fixed = TRUE)[[1]]
  cn <- unname(iso[cc]); cn <- cn[!is.na(cn)]
  if (uniq) cn <- unique(cn)
  if (!length(cn)) NA_character_ else paste(cn, collapse = ";")
}
up <- function(x) { x <- toupper(iconv(x, "UTF-8", "ASCII//TRANSLIT", sub = "")); x[is.na(x)] <- ""; x }
nz <- function(x) ifelse(is.na(x) | x == "", NA_character_, x)

M <- data.frame(
  AU = nz(m$AU), AF = nz(up(gsub("; ", ";", m$authors))), TI = up(m$title), SO = m$SO, JI = m$SO, J9 = m$SO,
  DT = toupper(m$doc_type), DE = nz(if ("author_keywords" %in% names(m)) up(gsub("; ", ";", m$author_keywords)) else NA_character_),
  ID = nz(up(gsub("; ", ";", m$openalex_keywords))), AB = nz(up(m$abstract)),
  C1 = vapply(m$affil_pairs, pair2c1, ""), RP = vapply(m$reprint_affil, pair2c1, ""),
  CR = nz(m$CR), TC = as.numeric(m$cited_by), PY = as.numeric(m$year), DI = nz(toupper(m$doi)),
  UT = m$id, SR = m$SR, SR_FULL = m$SR, DB = "ISI", LA = "ENGLISH", PU = NA_character_,
  NR = as.numeric(m$refs_listed),
  AU_UN = nz(up(gsub("; ", ";", m$institutions))),
  AU_CO = vapply(m$author_countries_all, codes2names, ""),
  AU1_CO = vapply(m$corresponding_country, codes2names, ""),
  SUBLIT = m$primary_sublit, SUBLITS = m$sublits, LCS_EXACT = as.numeric(m$local_citations),
  TOPIC = m$openalex_topic, stringsAsFactors = FALSE)
M$AU1_UN <- vapply(strsplit(ifelse(is.na(M$AU_UN), "", M$AU_UN), ";"), function(z) if (length(z)) z[1] else NA_character_, "")
M$TC[is.na(M$TC)] <- 0
M <- M[!is.na(M$PY), ]
rownames(M) <- M$SR
class(M) <- c("bibliometrixDB", "data.frame")
saveRDS(M, file.path(CLEAN, "M.rds"))
saveRDS(m, file.path(CLEAN, "master.rds"))
cat("M:", nrow(M), "x", ncol(M), "| with CR:", sum(!is.na(M$CR)), "| with country:", sum(!is.na(M$AU_CO)),
    "| with keywords:", sum(!is.na(M$ID)), "\n")
