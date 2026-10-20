# Task 10, step 3: load the Scopus export into Bibliometrix (raw 168 and cleaned 155).
# Usage: Rscript t10_03_scopus_M.R
.a <- commandArgs(FALSE); source(file.path(dirname(sub("^--file=", "", .a[grep("^--file=", .a)])), "common.R"))

prep <- function(file, out) {
  M <- convert2df(file.path(CLEAN, file), dbsource = "scopus", format = "csv")
  M <- metaTagExtraction(M, Field = "AU_CO", sep = ";")
  M <- metaTagExtraction(M, Field = "AU1_CO", sep = ";")
  M <- metaTagExtraction(M, Field = "AU_UN", sep = ";")
  if (!("SR" %in% names(M))) M <- metaTagExtraction(M, Field = "SR", sep = ";")
  M$TC <- as.numeric(M$TC); M$TC[is.na(M$TC)] <- 0; M$PY <- as.numeric(M$PY)
  saveRDS(M, file.path(CLEAN, out))
  cat(out, ":", nrow(M), "records |", sum(!is.na(M$DE) & M$DE != ""), "with author keywords |", sum(!is.na(M$AU_CO)), "with country |",
      sum(!is.na(M$CR) & M$CR != ""), "with references\n")
  invisible(M)
}
Mr <- prep("scopus_168.csv", "M_scopus_raw.rds")
Mc <- prep("scopus_clean.csv", "M_scopus_clean.rds")
