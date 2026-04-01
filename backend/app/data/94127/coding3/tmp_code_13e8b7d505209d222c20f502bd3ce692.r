exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-5: Differential expression analysis using limma::topTable
# Constraints: use only allowlisted inputs; graceful handling for missing files.

suppressPackageStartupMessages({
  library(limma)
  library(data.table)
})

# Allowlisted inputs for this task (strict)
allowlist <- c(
  "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  "/workspace/data/GSE230773_Read_counts.xlsx",
  "/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
  "/workspace/data/GSE247026_Sample_genes_fpkm.xlsx",
  "/workspace/data/GSE55465_non-normalized_INT-B.txt.gz",
  "/workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz"
)

# Expected empirical Bayes object from previous step
ebayes_rds <- "/workspace/coding3/part3_dry_experiment_4_ebayes_fit.rds"

# Output paths
out_degs <- "/workspace/coding3/part3_dry_experiment_5_degs.csv"
out_log  <- "/workspace/coding3/part3_dry_experiment_5_log.txt"

log_lines <- c(
  paste0("Part 3-dry-experiment-5 started at: ", Sys.time()),
  paste0("Expected eBayes RDS: ", ebayes_rds)
)

# Helper: placeholder output
write_placeholder <- function(reason) {
  log_lines <<- c(log_lines, paste0("WARNING: ", reason))
  placeholder <- data.frame(
    gene_id = character(),
    logFC = numeric(),
    adj.P.Val = numeric(),
    stringsAsFactors = FALSE
  )
  write.csv(placeholder, out_degs, row.names = FALSE)
  log_lines <<- c(log_lines, paste0("Placeholder DEGs file written: ", out_degs))
}

# Enforce allowlist rule: do not read non-allowlisted inputs
if (!ebayes_rds %in% allowlist) {
  write_placeholder("Empirical Bayes object path is not in the allowlisted inputs; skipping load.")
} else if (!file.exists(ebayes_rds)) {
  write_placeholder("Empirical Bayes object not found; skipping load.")
} else {
  # Attempt to load and run topTable
  fit <- tryCatch(readRDS(ebayes_rds), error = function(e) e)
  if (inherits(fit, "error")) {
    write_placeholder(paste0("Failed to read eBayes object: ", fit$message))
  } else {
    # Use topTable to get all genes, then filter by criteria
    tt <- tryCatch(
      topTable(fit, number = Inf, adjust.method = "BH", sort.by = "P"),
      error = function(e) e
    )
    if (inherits(tt, "error")) {
      write_placeholder(paste0("topTable failed: ", tt$message))
    } else {
      # Determine gene identifier column
      tt$gene_id <- if (!is.null(rownames(tt))) rownames(tt) else seq_len(nrow(tt))

      # Filter by adjusted P-value < 0.001 and |log2FC| > 1
      degs <- tt[!is.na(tt$adj.P.Val) &
                  !is.na(tt$logFC) &
                  tt$adj.P.Val < 0.001 &
                  abs(tt$logFC) > 1, c("gene_id", "logFC", "adj.P.Val")]

      # Ensure data.frame
      degs <- as.data.frame(degs)
      write.csv(degs, out_degs, row.names = FALSE)
      log_lines <- c(log_lines, paste0("DEGs identified: ", nrow(degs)))
      log_lines <- c(log_lines, paste0("DEGs saved to: ", out_degs))
    }
  }
}

log_lines <- c(log_lines, paste0("Part 3-dry-experiment-5 completed at: ", Sys.time()))
writeLines(log_lines, out_log)