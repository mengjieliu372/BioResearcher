exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 2-dry-experiment-2: QC on RNA-seq data (allowlisted inputs only)
# Outputs under /workspace/coding3

suppressPackageStartupMessages({
  library(data.table)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Input allowlist
f_meta <- "/workspace/data/GSE267611_sample_meta_out.txt.gz"
f_counts <- "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz"
f_cytolytic <- "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"

# Helper: safe read
safe_fread <- function(path, ...) {
  if (!file.exists(path)) {
    warning(sprintf("Missing file: %s", path))
    return(NULL)
  }
  tryCatch({
    data.table::fread(path, ...)
  }, error = function(e) {
    warning(sprintf("Failed to read %s: %s", path, e$message))
    NULL
  })
}

# Read inputs
meta_dt <- safe_fread(f_meta)
counts_dt <- safe_fread(f_counts)
cyto_dt <- safe_fread(f_cytolytic)

# Build a shared sample schema from available sources
schema_cols <- c("sample_id", "source", "notes")
sample_list <- list()

# From counts matrix (columns are samples; first column likely gene IDs)
if (!is.null(counts_dt) && ncol(counts_dt) > 1) {
  sample_ids <- colnames(counts_dt)[-1]
  sample_list[["counts"]] <- data.table(sample_id = sample_ids,
                                        source = "GSE91061_raw_counts",
                                        notes = NA_character_)
}

# From cytolytic score file
if (!is.null(cyto_dt) && ncol(cyto_dt) >= 1) {
  # guess sample id column: use first column name
  cyto_sample_col <- colnames(cyto_dt)[1]
  sample_list[["cytolytic"]] <- data.table(sample_id = as.character(cyto_dt[[cyto_sample_col]]),
                                           source = "GSE91061_cytolytic_score",
                                           notes = NA_character_)
}

# From metadata file
if (!is.null(meta_dt)) {
  # attempt to find sample id column
  cand_cols <- intersect(tolower(colnames(meta_dt)), c("sample", "sample_id", "gsm", "geo_accession"))
  if (length(cand_cols) > 0) {
    col_use <- colnames(meta_dt)[match(cand_cols[1], tolower(colnames(meta_dt)))]
    sample_list[["meta"]] <- data.table(sample_id = as.character(meta_dt[[col_use]]),
                                        source = "GSE267611_meta",
                                        notes = NA_character_)
  }
}

if (length(sample_list) > 0) {
  sample_dt <- data.table::rbindlist(sample_list, fill = TRUE)
  sample_dt <- unique(sample_dt)
} else {
  sample_dt <- data.table(sample_id = character(), source = character(), notes = character())
}

# QC metrics from counts
qc_metrics <- data.table()
excluded <- data.table()

if (!is.null(counts_dt) && ncol(counts_dt) > 1) {
  gene_ids <- counts_dt[[1]]
  count_mat <- as.matrix(counts_dt[, -1, with = FALSE])
  rownames(count_mat) <- gene_ids

  # Basic metrics
  lib_size <- colSums(count_mat, na.rm = TRUE)
  detected_genes <- colSums(count_mat > 0, na.rm = TRUE)
  percent_zero <- colMeans(count_mat == 0, na.rm = TRUE) * 100

  # Placeholder 3'/5' ratio (not available)
  ratio_3_5 <- rep(NA_real_, length(lib_size))

  # Simple pass/fail criteria (adjustable)
  pass_lib <- lib_size > 1e6
  pass_detected <- detected_genes > 10000
  pass_ratio <- !is.na(ratio_3_5) & ratio_3_5 > 1.5
  pass_ratio[is.na(pass_ratio)] <- NA  # keep NA if ratio not available

  # Overall pass: require library size & detected genes; ratio if available
  overall_pass <- pass_lib & pass_detected
  # if ratio available, also require
  if (any(!is.na(pass_ratio))) {
    overall_pass <- overall_pass & pass_ratio
  }

  qc_metrics <- data.table(
    sample_id = colnames(count_mat),
    library_size = lib_size,
    detected_genes = detected_genes,
    percent_zero = percent_zero,
    ratio_3_5 = ratio_3_5,
    pass_library_size = pass_lib,
    pass_detected_genes = pass_detected,
    pass_ratio_3_5 = pass_ratio,
    overall_pass = overall_pass
  )

  excluded <- qc_metrics[overall_pass == FALSE, .(sample_id, reason = "Failed library_size/detected_genes thresholds or ratio if available")]
} else {
  warning("Counts matrix not available or empty; QC metrics will be placeholders.")
  qc_metrics <- data.table(
    sample_id = character(),
    library_size = numeric(),
    detected_genes = numeric(),
    percent_zero = numeric(),
    ratio_3_5 = numeric(),
    pass_library_size = logical(),
    pass_detected_genes = logical(),
    pass_ratio_3_5 = logical(),
    overall_pass = logical()
  )
  excluded <- data.table(sample_id = character(), reason = character())
}

# RNA degradation plot (approximate using mean expression by gene rank)
plot_path <- file.path(out_dir, "rna_degradation_plot.png")
png(plot_path, width = 1200, height = 800)
if (!is.null(counts_dt) && ncol(counts_dt) > 1) {
  mean_expr <- rowMeans(as.matrix(counts_dt[, -1, with = FALSE]), na.rm = TRUE)
  ord <- order(mean_expr, decreasing = TRUE)
  # Bin into 100 quantiles
  bins <- cut(seq_along(mean_expr), breaks = 100, labels = FALSE)
  mean_by_bin <- tapply(mean_expr[ord], bins, mean, na.rm = TRUE)
  plot(mean_by_bin, type = "l", col = "steelblue", lwd = 2,
       xlab = "Gene expression rank bin (high to low)",
       ylab = "Mean expression",
       main = "RNA degradation proxy plot\n(mean expression by rank bin)")
  mtext("Note: No explicit 3'/5' ratios available; this is a proxy visualization.", side = 3, line = 0.5, cex = 0.8)
} else {
  plot.new()
  text(0.5, 0.5, "RNA degradation plot unavailable\n(counts matrix missing)", cex = 1.2)
}
dev.off()

# QC report
report_path <- file.path(out_dir, "qc_report.txt")
report_lines <- c(
  "QC Report: RNA sequencing data",
  sprintf("Generated: %s", Sys.time()),
  "",
  "Inputs:",
  sprintf("- %s (exists: %s)", f_counts, file.exists(f_counts)),
  sprintf("- %s (exists: %s)", f_cytolytic, file.exists(f_cytolytic)),
  sprintf("- %s (exists: %s)", f_meta, file.exists(f_meta)),
  "",
  "QC metrics summary:"
)

if (nrow(qc_metrics) > 0) {
  total_samples <- nrow(qc_metrics)
  pass_samples <- sum(qc_metrics$overall_pass, na.rm = TRUE)
  fail_samples <- sum(qc_metrics$overall_pass == FALSE, na.rm = TRUE)
  na_ratio <- sum(is.na(qc_metrics$ratio_3_5))
  report_lines <- c(report_lines,
                    sprintf("Total samples evaluated: %d", total_samples),
                    sprintf("Passing samples: %d", pass_samples),
                    sprintf("Failing samples: %d", fail_samples),
                    sprintf("Samples with missing 3'/5' ratio: %d", na_ratio),
                    "",
                    "Thresholds used:",
                    "- Library size > 1e6",
                    "- Detected genes > 10,000",
                    "- 3'/5' ratio > 1.5 (if available)",
                    "",
                    "RNA degradation plot saved to:",
                    plot_path)
} else {
  report_lines <- c(report_lines,
                    "No samples evaluated due to missing counts matrix.",
                    sprintf("RNA degradation plot saved to: %s (placeholder)", plot_path))
}

writeLines(report_lines, con = report_path)

# Save outputs
data.table::fwrite(qc_metrics, file.path(out_dir, "qc_metrics.csv"))
data.table::fwrite(excluded, file.path(out_dir, "qc_excluded_samples.csv"))

# Also save combined sample list (optional for traceability)
data.table::fwrite(sample_dt, file.path(out_dir, "qc_sample_sources_combined.csv"))

# Message to console
cat("QC completed. Outputs:\n",
    "- ", report_path, "\n",
    "- ", file.path(out_dir, "qc_metrics.csv"), "\n",
    "- ", file.path(out_dir, "qc_excluded_samples.csv"), "\n",
    "- ", plot_path, "\n",
    "- ", file.path(out_dir, "qc_sample_sources_combined.csv"), "\n", sep = "")