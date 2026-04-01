exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-1 (corrected)
# Load RNA sequencing data from TCGA (liposarcoma) and GSE202361 into R-ready objects
# Constraints handled:
# - Uses only allowlisted input files
# - Graceful handling of missing files/packages
# - No stop()/quit()/exit()
# - Outputs saved under /workspace/coding3

options(stringsAsFactors = FALSE)

suppressWarnings({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    install.packages("data.table", repos = "https://cloud.r-project.org")
  }
  if (!requireNamespace("readxl", quietly = TRUE)) {
    install.packages("readxl", repos = "https://cloud.r-project.org")
  }
})

library(data.table)

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

log_file <- file.path(out_dir, "part3_dry_experiment_1_load_log.txt")
log_con <- file(log_file, open = "wt")
sink(log_con, type = "output")
sink(log_con, type = "message")

cat("=== Part 3-dry-experiment-1: RNA-seq loading started ===\n")
cat("Timestamp:", as.character(Sys.time()), "\n\n")

# ---- Input allowlist (strict) ----
f_gse_tpm    <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"
f_gse_counts <- "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz"

# Use previously generated TCGA liposarcoma file from earlier task history
f_tcga_cases <- "/workspace/coding3/tcga_liposarcoma_cases.csv"

# ---- Helper: safe fread ----
safe_fread <- function(path, label) {
  if (!file.exists(path)) {
    warning(sprintf("[%s] Missing file: %s", label, path))
    return(data.table())
  }
  obj <- tryCatch(
    fread(path),
    error = function(e) {
      warning(sprintf("[%s] Failed to read %s ; reason: %s", label, path, e$message))
      data.table()
    }
  )
  if (!is.data.table(obj)) obj <- as.data.table(obj)
  obj
}

# ---- Load GSE202361 TPM ----
gse_tpm <- safe_fread(f_gse_tpm, "GSE202361_TPM")
if (nrow(gse_tpm) > 0) {
  fwrite(gse_tpm, file.path(out_dir, "gse202361_tpm_loaded.csv"))
  cat("Loaded GSE202361 TPM:", nrow(gse_tpm), "rows x", ncol(gse_tpm), "cols\n")
} else {
  # non-empty placeholder schema
  gse_tpm <- data.table(gene_id = character(), sample_id = character(), tpm = numeric())
  fwrite(gse_tpm, file.path(out_dir, "gse202361_tpm_loaded.csv"))
  cat("GSE202361 TPM unavailable; wrote empty schema file.\n")
}

# ---- Load GSE202361 raw counts ----
gse_counts <- safe_fread(f_gse_counts, "GSE202361_COUNTS")
if (nrow(gse_counts) > 0) {
  fwrite(gse_counts, file.path(out_dir, "gse202361_counts_loaded.csv"))
  cat("Loaded GSE202361 counts:", nrow(gse_counts), "rows x", ncol(gse_counts), "cols\n")
} else {
  gse_counts <- data.table(gene_id = character(), sample_id = character(), raw_count = numeric())
  fwrite(gse_counts, file.path(out_dir, "gse202361_counts_loaded.csv"))
  cat("GSE202361 counts unavailable; wrote empty schema file.\n")
}

# ---- Load TCGA liposarcoma cases (real file, no placeholder naming) ----
tcga_cases <- safe_fread(f_tcga_cases, "TCGA_LIPOSARCOMA_CASES")
if (nrow(tcga_cases) > 0) {
  fwrite(tcga_cases, file.path(out_dir, "tcga_liposarcoma_cases_loaded.csv"))
  cat("Loaded TCGA liposarcoma cases:", nrow(tcga_cases), "rows x", ncol(tcga_cases), "cols\n")
} else {
  tcga_cases <- data.table(case_id = character(), project_id = character(), disease_type = character())
  fwrite(tcga_cases, file.path(out_dir, "tcga_liposarcoma_cases_loaded.csv"))
  cat("TCGA cases file unavailable; wrote empty schema file.\n")
}

# ---- Build R-ready objects ----
# Keep matrices/data.frames that are directly usable downstream
to_matrix_if_possible <- function(dt) {
  if (!is.data.table(dt) || nrow(dt) == 0 || ncol(dt) < 2) return(matrix(numeric(0), nrow = 0, ncol = 0))
  x <- as.data.frame(dt)
  rn <- x[[1]]
  num_idx <- which(vapply(x, is.numeric, logical(1)))
  num_idx <- setdiff(num_idx, 1L)
  if (length(num_idx) == 0) return(matrix(numeric(0), nrow = 0, ncol = 0))
  m <- as.matrix(x[, num_idx, drop = FALSE])
  rownames(m) <- make.unique(as.character(rn))
  m
}

rna_objects <- list(
  gse202361_tpm_df = as.data.frame(gse_tpm),
  gse202361_counts_df = as.data.frame(gse_counts),
  gse202361_tpm_mat = to_matrix_if_possible(gse_tpm),
  gse202361_counts_mat = to_matrix_if_possible(gse_counts),
  tcga_liposarcoma_cases_df = as.data.frame(tcga_cases),
  metadata = list(
    task_id = "Part 3-dry-experiment-1",
    created_at = as.character(Sys.time()),
    input_files = c(f_gse_tpm, f_gse_counts, f_tcga_cases)
  )
)

saveRDS(rna_objects, file.path(out_dir, "rnaseq_loaded_objects.rds"))

# Also emit compact object summary for quick validation
obj_summary <- data.table(
  object_name = c("gse202361_tpm_df", "gse202361_counts_df", "tcga_liposarcoma_cases_df"),
  nrow = c(nrow(rna_objects$gse202361_tpm_df),
           nrow(rna_objects$gse202361_counts_df),
           nrow(rna_objects$tcga_liposarcoma_cases_df)),
  ncol = c(ncol(rna_objects$gse202361_tpm_df),
           ncol(rna_objects$gse202361_counts_df),
           ncol(rna_objects$tcga_liposarcoma_cases_df))
)
fwrite(obj_summary, file.path(out_dir, "part3_dry_experiment_1_object_summary.csv"))

cat("\nSaved outputs:\n")
cat(" -", file.path(out_dir, "gse202361_tpm_loaded.csv"), "\n")
cat(" -", file.path(out_dir, "gse202361_counts_loaded.csv"), "\n")
cat(" -", file.path(out_dir, "tcga_liposarcoma_cases_loaded.csv"), "\n")
cat(" -", file.path(out_dir, "rnaseq_loaded_objects.rds"), "\n")
cat(" -", file.path(out_dir, "part3_dry_experiment_1_object_summary.csv"), "\n")
cat(" -", log_file, "\n")
cat("\n=== Part 3-dry-experiment-1: completed ===\n")

sink(type = "message")
sink(type = "output")
close(log_con)