exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part5-dry-experiment-1-saved
# Task: Acquire TCGA-like RNA-seq data focusing on lncRNAs and immune checkpoints (proxy from allowlisted files)
# Constraints: use only allowlisted input files; graceful handling; outputs under /workspace/coding3

set.seed(1)
options(stringsAsFactors = FALSE)

suppressPackageStartupMessages({
  library(data.table)
})

log_file <- "/workspace/coding3/part5_dry_experiment_1_log.txt"
expr_out <- "/workspace/coding3/part5_dry_experiment_1_lncrna_icm_expression.csv"
clin_out <- "/workspace/coding3/part5_dry_experiment_1_clinical_attributes.csv"

cat(sprintf("Part 5-dry-experiment-1 started at: %s\n", Sys.time()),
    file = log_file)

# Allowed input (strict)
tpm_file <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"

# Immune checkpoint genes of interest
icm_genes <- c("PDCD1", "CD274", "CTLA4", "PDCD1LG2", "LAG3", "TIGIT", "HAVCR2", "BTLA", "IDO1")

# Heuristic lncRNA gene symbols (common prefixes/known lncRNAs)
lnc_patterns <- c("^LINC", "^MIR", "^SNHG", "^MEG", "^NEAT1$", "^MALAT1$", "^XIST$", "^HOTAIR$", "^PVT1$")
lnc_regex <- paste(lnc_patterns, collapse = "|")

# Initialize placeholders
expr_dt <- NULL
clin_dt <- NULL
used_proxy <- FALSE

if (file.exists(tpm_file)) {
  cat(sprintf("[%s] Found TPM file: %s\n", Sys.time(), tpm_file), file = log_file, append = TRUE)

  # Read TPM matrix
  # Expect first column as gene identifier
  tpm_dt <- tryCatch({
    fread(tpm_file)
  }, error = function(e) {
    cat(sprintf("[%s] Warning: failed to read TPM file: %s\n", Sys.time(), e$message),
        file = log_file, append = TRUE)
    NULL
  })

  if (!is.null(tpm_dt) && ncol(tpm_dt) >= 2) {
    gene_col <- names(tpm_dt)[1]
    setnames(tpm_dt, gene_col, "gene_id")

    # Identify immune checkpoint rows
    icm_rows <- tpm_dt[gene_id %in% icm_genes]

    # Identify putative lncRNA rows by heuristic symbol patterns
    lnc_rows <- tpm_dt[grepl(lnc_regex, gene_id, ignore.case = FALSE)]

    # Combine and deduplicate
    expr_dt <- unique(rbindlist(list(icm_rows, lnc_rows), fill = TRUE))

    if (nrow(expr_dt) == 0) {
      cat(sprintf("[%s] Warning: No ICM or lncRNA genes detected; creating placeholder\n", Sys.time()),
          file = log_file, append = TRUE)
      expr_dt <- data.table(gene_id = c(icm_genes, "LINC_PLACEHOLDER"))
    } else {
      used_proxy <- TRUE
      cat(sprintf("[%s] Extracted %d genes (ICM+lncRNA proxy)\n",
                  Sys.time(), nrow(expr_dt)),
          file = log_file, append = TRUE)
    }

    # Build clinical attributes placeholder from sample IDs
    sample_ids <- setdiff(names(tpm_dt), "gene_id")
    clin_dt <- data.table(
      sample_id = sample_ids,
      age = NA_real_,
      sex = NA_character_,
      tumor_grade = NA_character_,
      stage = NA_character_,
      treatment_history = NA_character_,
      source_note = if (used_proxy) "Proxy from GSE202361 TPM (no TCGA clinical metadata available)" else "Placeholder"
    )
  } else {
    cat(sprintf("[%s] Warning: TPM file has insufficient columns; using placeholders\n", Sys.time()),
        file = log_file, append = TRUE)
  }
} else {
  cat(sprintf("[%s] Warning: TPM file not found; using placeholders\n", Sys.time()),
      file = log_file, append = TRUE)
}

# Fallback placeholders if needed
if (is.null(expr_dt)) {
  expr_dt <- data.table(
    gene_id = c(icm_genes, "LINC_PLACEHOLDER"),
    placeholder_sample = NA_real_
  )
}
if (is.null(clin_dt)) {
  clin_dt <- data.table(
    sample_id = "SAMPLE_PLACEHOLDER",
    age = NA_real_,
    sex = NA_character_,
    tumor_grade = NA_character_,
    stage = NA_character_,
    treatment_history = NA_character_,
    source_note = "Placeholder (no clinical metadata available)"
  )
}

# Write outputs
fwrite(expr_dt, expr_out)
fwrite(clin_dt, clin_out)

cat(sprintf("[%s] Expression output saved: %s (rows=%d, cols=%d)\n",
            Sys.time(), expr_out, nrow(expr_dt), ncol(expr_dt)),
    file = log_file, append = TRUE)
cat(sprintf("[%s] Clinical attributes output saved: %s (rows=%d)\n",
            Sys.time(), clin_out, nrow(clin_dt)),
    file = log_file, append = TRUE)
cat(sprintf("Part 5-dry-experiment-1 completed at: %s\n", Sys.time()),
    file = log_file, append = TRUE)