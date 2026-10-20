# Shared helpers for the Bibliometrix scripts (identical copy in each paper folder).
# Extra packages live in a library on D: (never installed to C:).
.libPaths(c("D:/Research-Publishing/_tools/R-lib", .libPaths()))
if (!dir.exists("D:/")) stop("D: is not mounted - stopping.")
suppressPackageStartupMessages({
  library(bibliometrix); library(ggplot2); library(dplyr); library(tidyr); library(stringr)
  library(igraph); library(Matrix); library(data.table); library(jsonlite); library(ggrepel)
})
options(stringsAsFactors = FALSE, warn = 1, width = 160)

.args <- commandArgs(FALSE)
.file <- sub("^--file=", "", .args[grep("^--file=", .args)])
BASE  <- normalizePath(file.path(dirname(.file), ".."), winslash = "/")
FIG   <- file.path(BASE, "figures"); TAB <- file.path(BASE, "tables"); CLEAN <- file.path(BASE, "data", "clean")
for (d in c(FIG, TAB, CLEAN)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

CAPS <- list(); FAILS <- list()
cap <- function(file, title, what, how, caution) {
  CAPS[[length(CAPS) + 1]] <<- list(file = file, title = title, what = what, how = how, caution = caution)
}
save_caps <- function(name) {
  write_json(CAPS, file.path(FIG, paste0("captions_", name, ".json")), auto_unbox = TRUE, pretty = TRUE)
  if (length(FAILS)) writeLines(paste(names(FAILS), unlist(FAILS), sep = " :: "),
                                file.path(TAB, paste0("R_failures_", name, ".txt")))
  else if (file.exists(file.path(TAB, paste0("R_failures_", name, ".txt")))) file.remove(file.path(TAB, paste0("R_failures_", name, ".txt")))
}
safe <- function(name, expr) {
  t0 <- Sys.time()
  out <- tryCatch(withCallingHandlers(expr, warning = function(w) invokeRestart("muffleWarning")),
                  error = function(e) {
                    message("!! ", name, " FAILED: ", conditionMessage(e))
                    FAILS[[name]] <<- conditionMessage(e)
                    while (dev.cur() > 1) dev.off()
                    NULL
                  })
  message(sprintf("[%s] %.1fs", name, as.numeric(difftime(Sys.time(), t0, units = "secs"))))
  invisible(out)
}
theme_bm <- function(base = 11) {
  theme_minimal(base_size = base) +
    theme(plot.title = element_text(face = "bold", size = base + 3), plot.subtitle = element_text(colour = "grey30"),
          plot.caption = element_text(colour = "grey40", size = base - 3, hjust = 0),
          panel.grid.minor = element_blank(), legend.position = "bottom",
          plot.background = element_rect(fill = "white", colour = NA))
}
gsave <- function(p, file, w = 10, h = 6.5, svg = FALSE) {
  ggsave(file.path(FIG, paste0(file, ".png")), p, width = w, height = h, dpi = 220, bg = "white", limitsize = FALSE)
  if (svg) try(ggsave(file.path(FIG, paste0(file, ".svg")), p, width = w, height = h, bg = "white"), silent = TRUE)
}
pngdev <- function(file, w = 11, h = 9) png(file.path(FIG, paste0(file, ".png")), width = w, height = h, units = "in", res = 220, bg = "white")
wtab <- function(df, file) write.csv(as.data.frame(df), file.path(TAB, paste0(file, ".csv")), row.names = FALSE, fileEncoding = "UTF-8", na = "")
trunc_lab <- function(x, n = 55) ifelse(nchar(x) > n, paste0(substr(x, 1, n - 1), "\u2026"), x)
explode <- function(x, sep = ";") {
  l <- strsplit(ifelse(is.na(x), "", x), sep, fixed = TRUE)
  data.frame(row = rep(seq_along(l), lengths(l)), value = trimws(unlist(l))) |> filter(value != "", value != "NA")
}
PAL <- c("#1b6ca8", "#d1495b", "#2e933c", "#edae49", "#6a4c93", "#00798c", "#8d6e63", "#e76f51", "#5c6bc0", "#7cb342",
         "#c2185b", "#00897b", "#f4511e", "#546e7a", "#9e9d24")
