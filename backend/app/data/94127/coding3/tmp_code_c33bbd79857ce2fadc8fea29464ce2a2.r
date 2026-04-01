exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-1: Load RNA sequencing data from TCGA and GSE202361
# Constraints: use only allowlisted inputs, graceful handling, save outputs under /workspace/coding3

# Load required libraries (install minimal if missing)
if (!requireNamespace("data.table", quietly = TRUE)) {
  install.packages("data.table")
}
if (!requireNamespace("tximport", quietly = TRUE)) {
  install.packages("tximport")
}

library(data.table)

# Define input paths (allowlisted)
gse202361_tpm_path <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"
gse202361_counts_path <- "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz"

# Output paths
out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

gse202361_tpm_out <- file.path(out_dir, "gse202361_tpm_loaded.csv")
gse202361_counts_out <- file.path(out_dir, "gse202361_counts_loaded.csv")
tcga_placeholder_out <- file.path(out_dir, "tcga_liposarcoma_placeholder.csv")
combined_rds_out <- file.path(out_dir, "rnaseq_loaded_objects.rds")
log_out <- file.path(out_dir, "part3_dry_experiment_1_load_log.txt")

log_lines <- c()

# Helper to read gz tables gracefully
read_gz_table <- function(path) {
  if (!file.exists(path)) {
    log_lines <<- c(log_lines, paste("WARNING: Missing file:", path))
    return(NULL)
  }
  # fread can read gz directly
  dt <- tryCatch({
    fread(path)
  }, error = function(e) {
    log_lines <<- c(log_lines, paste("WARNING: Failed to read", path, ":", e$message))
    return(NULL)
  })
  return(dt)
}

# Load GSE202361 TPM and raw counts
gse202361_tpm <- read_gz_table(gse202361_tpm_path)
gse202361_counts <- read_gz_table(gse202361_counts_path)

# Save outputs (even if NULL, create placeholder)
if (!is.null(gse202361_tpm)) {
  fwrite(gse202361_tpm, gse202361_tpm_out)
  log_lines <- c(log_lines, paste("Loaded GSE202361 TPM:", nrow(gse202361_tpm), "rows,", ncol(gse202361_tpm), "cols"))
} else {
  fwrite(data.table(), gse202361_tpm_out)
  log_lines <- c(log_lines, "Created placeholder for GSE202361 TPM (empty).")
}

if (!is.null(gse202361_counts)) {
  fwrite(gse202361_counts, gse202361_counts_out)
  log_lines <- c(log_lines, paste("Loaded GSE202361 raw counts:", nrow(gse202361_counts), "rows,", ncol(gse202361_counts), "cols"))
} else {
  fwrite(data.table(), gse202361_counts_out)
  log_lines <- c(log_lines, "Created placeholder for GSE202361 counts (empty).")
}

# TCGA liposarcoma data not available in allowlisted inputs: create placeholder
tcga_placeholder <- data.table(
  sample_id = character(),
  gene_id = character(),
  value = numeric(),
  metric = character()
)
fwrite(tcga_placeholder, tcga_placeholder_out)
log_lines <- c(log_lines, "TCGA liposarcoma RNA-seq not in allowlisted inputs; placeholder created.")

# Save combined R objects for downstream analysis
combined_objects <- list(
  gse202361_tpm = gse202361_tpm,
  gse202361_counts = gse202361_counts,
  tcga_liposarcoma = tcga_placeholder
)
saveRDS(combined_objects, combined_rds_out)
log_lines <- c(log_lines, paste("Saved combined objects to:", combined_rds_out))

# Write log
writeLines(log_lines, log_out)

# Print summary
cat("Part 3-dry-experiment-1 completed.\n",
    "Outputs:\n",
    " - ", gse202361_tpm_out, "\n",
    " - ", gse202361_counts_out, "\n",
    " - ", tcga_placeholder_out, "\n",
    " - ", combined_rds_out, "\n",
    " - ", log_out, "\n", sep = "")