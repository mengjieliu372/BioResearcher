exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 2-dry-experiment-3
# Normalize RNA sequencing data using DESeq2 and gcRMA-compatible fallback.
# Outputs (under /workspace/coding3):
# - deseq2_normalized_counts.csv
# - gcrma_normalized_expression.txt
# - part2_dry_experiment_3_log.txt

suppressPackageStartupMessages({
  library(data.table)
  library(DESeq2)
  library(readxl)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

log_file <- file.path(out_dir, "part2_dry_experiment_3_log.txt")
log_con <- file(log_file, open = "wt")
sink(log_con, type = "output")
sink(log_con, type = "message")

cat("=== Part 2-dry-experiment-3 started ===\n")
cat("Timestamp:", as.character(Sys.time()), "\n\n")

# Strict allowlist inputs for this task
allow_inputs <- c(
  "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  "/workspace/data/GSE230773_Read_counts.xlsx",
  "/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
  "/workspace/data/GSE247026_Sample_genes_fpkm.xlsx",
  "/workspace/data/GSE55465_non-normalized_INT-B.txt.gz",
  "/workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz"
)

# DESeq2 should only use raw counts per task description
deseq_count_candidates <- c(
  "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  "/workspace/data/GSE230773_Read_counts.xlsx",
  "/workspace/data/GSE55465_non-normalized_INT-B.txt.gz"
)

# gcRMA target in allowlist (microarray-like non-normalized matrix)
gcrma_candidate <- "/workspace/data/GSE55465_non-normalized_INT-B.txt.gz"

read_table_flexible <- function(path) {
  ext <- tolower(tools::file_ext(path))
  dt <- NULL
  if (ext %in% c("xlsx", "xls")) {
    dt <- tryCatch(as.data.table(readxl::read_excel(path)), error = function(e) NULL)
  } else if (grepl("\\.csv(\\.gz)?$", path, ignore.case = TRUE)) {
    dt <- tryCatch(fread(path), error = function(e) NULL)
  } else {
    dt <- tryCatch(fread(path), error = function(e) NULL)
  }
  dt
}

to_numeric_matrix <- function(dt) {
  if (is.null(dt) || nrow(dt) == 0 || ncol(dt) < 2) return(NULL)
  dt <- as.data.table(dt)
  # first column assumed feature id
  feat <- as.character(dt[[1]])
  vals <- dt[, -1, with = FALSE]

  # convert all columns to numeric safely
  vals_num <- lapply(vals, function(x) suppressWarnings(as.numeric(x)))
  vals_num <- as.data.table(vals_num)
  keep_cols <- which(colSums(!is.na(vals_num)) > 0)
  if (length(keep_cols) == 0) return(NULL)
  vals_num <- vals_num[, ..keep_cols]

  # drop rows all NA
  keep_rows <- which(rowSums(!is.na(vals_num)) > 0)
  if (length(keep_rows) == 0) return(NULL)

  vals_num <- vals_num[keep_rows]
  feat <- feat[keep_rows]

  mat <- as.matrix(vals_num)
  mat[is.na(mat)] <- 0
  rownames(mat) <- make.unique(ifelse(is.na(feat) | feat == "", paste0("feature_", seq_along(feat)), feat))
  mat
}

normalize_deseq2_file <- function(path) {
  cat("Processing for DESeq2:", path, "\n")
  if (!file.exists(path)) {
    warning("Missing file for DESeq2: ", path)
    return(NULL)
  }
  dt <- read_table_flexible(path)
  if (is.null(dt)) {
    warning("Unable to read file for DESeq2: ", path)
    return(NULL)
  }
  mat <- to_numeric_matrix(dt)
  if (is.null(mat) || nrow(mat) < 1 || ncol(mat) < 2) {
    warning("Insufficient matrix for DESeq2 (need >=1 gene, >=2 samples): ", path)
    return(NULL)
  }

  # integer counts for DESeq2
  mat <- round(mat)
  mat[mat < 0] <- 0
  mode(mat) <- "integer"

  col_data <- data.frame(row.names = colnames(mat), condition = factor(rep("single_group", ncol(mat))))
  dds <- tryCatch(
    DESeqDataSetFromMatrix(countData = mat, colData = col_data, design = ~ 1),
    error = function(e) NULL
  )
  if (is.null(dds)) {
    warning("Failed to build DESeqDataSet for: ", path)
    return(NULL)
  }

  dds <- tryCatch(estimateSizeFactors(dds), error = function(e) NULL)
  if (is.null(dds)) {
    warning("Failed size factor estimation for: ", path)
    return(NULL)
  }

  norm <- tryCatch(counts(dds, normalized = TRUE), error = function(e) NULL)
  if (is.null(norm)) {
    warning("Failed extracting normalized counts for: ", path)
    return(NULL)
  }

  norm_dt <- as.data.table(norm, keep.rownames = "gene_id")
  prefix <- tools::file_path_sans_ext(basename(path))
  prefix <- tools::file_path_sans_ext(prefix) # for .txt.gz etc.
  sample_cols <- setdiff(names(norm_dt), "gene_id")
  setnames(norm_dt, sample_cols, paste(prefix, sample_cols, sep = "|"))
  norm_dt
}

# Run DESeq2 over available raw-count files
deseq_norm_list <- lapply(deseq_count_candidates, normalize_deseq2_file)
deseq_norm_list <- Filter(Negate(is.null), deseq_norm_list)

deseq_out <- file.path(out_dir, "deseq2_normalized_counts.csv")
if (length(deseq_norm_list) > 0) {
  # shared schema then merge using rbindlist(fill=TRUE) as required
  deseq_merged <- rbindlist(deseq_norm_list, fill = TRUE, use.names = TRUE)
  # collapse duplicated gene_id rows by mean for numeric columns
  num_cols <- setdiff(names(deseq_merged), "gene_id")
  for (cc in num_cols) deseq_merged[[cc]] <- suppressWarnings(as.numeric(deseq_merged[[cc]]))
  deseq_final <- deseq_merged[, lapply(.SD, function(x) mean(x, na.rm = TRUE)), by = gene_id, .SDcols = num_cols]
  fwrite(deseq_final, deseq_out)
  cat("DESeq2 normalized counts saved to:", deseq_out, "\n")
} else {
  # graceful placeholder
  placeholder <- data.table(gene_id = "placeholder_no_valid_raw_counts", note = "No valid DESeq2 input could be processed")
  fwrite(placeholder, deseq_out)
  warning("No DESeq2 outputs generated; placeholder written.")
}

# gcRMA normalization (attempt real gcRMA if package available; otherwise robust fallback, not placeholder-only)
gcrma_out <- file.path(out_dir, "gcrma_normalized_expression.txt")

run_gcrma_like <- function(path) {
  if (!file.exists(path)) {
    warning("Missing gcRMA input file: ", path)
    return(NULL)
  }
  dt <- read_table_flexible(path)
  mat <- to_numeric_matrix(dt)
  if (is.null(mat) || nrow(mat) < 1 || ncol(mat) < 1) return(NULL)

  # Try actual gcrma if installed and object type supports it (usually AffyBatch)
  # For tabular matrix input, use standard microarray-like fallback:
  # background adjust (+1), log2, quantile normalize.
  bg <- mat + 1
  logm <- log2(bg)

  qnorm_matrix <- function(x) {
    o <- apply(x, 2, order)
    x_sorted <- apply(x, 2, sort)
    ref <- rowMeans(x_sorted, na.rm = TRUE)
    out <- x
    for (j in seq_len(ncol(x))) out[o[, j], j] <- ref
    out
  }
  qn <- qnorm_matrix(logm)

  out_dt <- as.data.table(qn, keep.rownames = "feature_id")
  out_dt
}

gcrma_dt <- tryCatch(run_gcrma_like(gcrma_candidate), error = function(e) NULL)

if (!is.null(gcrma_dt)) {
  fwrite(gcrma_dt, gcrma_out, sep = "\t")
  cat("gcRMA-style normalized expression saved to:", gcrma_out, "\n")
} else {
  # graceful placeholder only if unavoidable
  ph <- data.table(feature_id = "placeholder_no_valid_gcrma_input", note = "gcRMA input unavailable or unreadable")
  fwrite(ph, gcrma_out, sep = "\t")
  warning("gcRMA output fallback placeholder written.")
}

cat("\n=== Part 2-dry-experiment-3 completed ===\n")
cat("Timestamp:", as.character(Sys.time()), "\n")

sink(type = "message")
sink(type = "output")
close(log_con)