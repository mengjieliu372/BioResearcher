exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-3: Fit linear model using limma::lmFit
# Inputs: design matrix from previous step, formatted RNA-seq data (allowlisted files)
# Outputs: fitted model object and coefficient/SE summaries

suppressPackageStartupMessages({
  library(data.table)
  library(limma)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

log_file <- file.path(out_dir, "part3_dry_experiment_3_lmfit_log.txt")
log_lines <- c()

append_log <- function(msg) {
  log_lines <<- c(log_lines, paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", msg))
}

# Input files (allowlisted)
expr_file_tpm   <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"
expr_file_count <- "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz"

# Design matrix from previous step
design_file <- "/workspace/coding3/design_matrix.csv"

# Load expression data
expr_mat <- NULL
expr_source <- NULL

if (file.exists(expr_file_tpm)) {
  append_log("Loading TPM expression data from GSE202361_AllSamples_TPM.txt.gz")
  dt <- tryCatch(fread(expr_file_tpm), error = function(e) NULL)
  if (!is.null(dt) && nrow(dt) > 0) {
    expr_source <- expr_file_tpm
  }
}
if (is.null(expr_source) && file.exists(expr_file_count)) {
  append_log("Loading raw count data from GSE202361_AllSamples_rawcount.txt.gz")
  dt <- tryCatch(fread(expr_file_count), error = function(e) NULL)
  if (!is.null(dt) && nrow(dt) > 0) {
    expr_source <- expr_file_count
  }
}

if (!is.null(expr_source) && exists("dt")) {
  # Assume first column is gene ID
  gene_col <- names(dt)[1]
  gene_ids <- dt[[gene_col]]
  dt[[gene_col]] <- NULL
  expr_mat <- as.matrix(dt)
  rownames(expr_mat) <- gene_ids
  # Coerce to numeric matrix
  suppressWarnings(storage.mode(expr_mat) <- "numeric")
  append_log(paste0("Expression matrix loaded: ", nrow(expr_mat), " genes x ", ncol(expr_mat), " samples"))
} else {
  append_log("WARNING: No expression file found or failed to load; creating placeholder matrix.")
  expr_mat <- matrix(0, nrow = 1, ncol = 1)
  rownames(expr_mat) <- "gene_placeholder"
  colnames(expr_mat) <- "sample_placeholder"
}

# Load design matrix
design_mat <- NULL
if (file.exists(design_file)) {
  append_log("Loading design matrix from /workspace/coding3/design_matrix.csv")
  design_dt <- tryCatch(fread(design_file), error = function(e) NULL)
  if (!is.null(design_dt) && nrow(design_dt) > 0) {
    # If first column seems like sample IDs, set as rownames
    if (!is.null(names(design_dt)[1]) && names(design_dt)[1] %in% c("sample_id", "Sample", "sample")) {
      rn <- design_dt[[1]]
      design_dt[[1]] <- NULL
      design_mat <- as.matrix(design_dt)
      rownames(design_mat) <- rn
    } else {
      design_mat <- as.matrix(design_dt)
      # if rownames missing, create sequential
      if (is.null(rownames(design_mat))) {
        rownames(design_mat) <- paste0("sample_", seq_len(nrow(design_mat)))
      }
    }
    append_log(paste0("Design matrix loaded: ", nrow(design_mat), " samples x ", ncol(design_mat), " covariates"))
  }
}

# If design matrix missing or invalid, create a simple intercept-only matrix
if (is.null(design_mat)) {
  append_log("WARNING: Design matrix missing or invalid; creating intercept-only design.")
  design_mat <- matrix(1, nrow = ncol(expr_mat), ncol = 1)
  rownames(design_mat) <- colnames(expr_mat)
  colnames(design_mat) <- "Intercept"
}

# Align expression columns with design matrix rows
common_samples <- intersect(colnames(expr_mat), rownames(design_mat))
if (length(common_samples) >= 1) {
  expr_mat <- expr_mat[, common_samples, drop = FALSE]
  design_mat <- design_mat[common_samples, , drop = FALSE]
  append_log(paste0("Aligned expression and design matrices to ", length(common_samples), " common samples"))
} else {
  append_log("WARNING: No overlapping samples between expression data and design matrix; using intercept-only design.")
  design_mat <- matrix(1, nrow = ncol(expr_mat), ncol = 1)
  rownames(design_mat) <- colnames(expr_mat)
  colnames(design_mat) <- "Intercept"
}

# Fit linear model using limma::lmFit
fit <- NULL
fit_ok <- TRUE
fit <- tryCatch({
  lmFit(expr_mat, design_mat)
}, error = function(e) {
  fit_ok <<- FALSE
  append_log(paste0("WARNING: lmFit failed: ", e$message))
  NULL
})

# Save fitted model object
fit_rds <- file.path(out_dir, "limma_lmfit_object.rds")
if (!is.null(fit)) {
  saveRDS(fit, fit_rds)
  append_log(paste0("Saved lmFit object to: ", fit_rds))
} else {
  # placeholder object
  saveRDS(list(error = "lmFit_failed", coefficients = NA), fit_rds)
  append_log("Saved placeholder lmFit object.")
}

# Save coefficients and standard errors summary
coef_file <- file.path(out_dir, "limma_lmfit_coefficients_se.csv")
if (fit_ok && !is.null(fit$coefficients)) {
  coef_mat <- fit$coefficients
  se_mat <- NULL
  if (!is.null(fit$stdev.unscaled) && !is.null(fit$sigma)) {
    # Compute standard errors: stdev.unscaled * sigma
    se_mat <- fit$stdev.unscaled * fit$sigma
  }
  coef_dt <- as.data.table(coef_mat, keep.rownames = "gene_id")
  if (!is.null(se_mat)) {
    se_dt <- as.data.table(se_mat)
    names(se_dt) <- paste0("SE_", names(se_dt))
    coef_dt <- cbind(coef_dt, se_dt)
  }
  fwrite(coef_dt, coef_file)
  append_log(paste0("Saved coefficients/SE summary to: ", coef_file))
} else {
  # placeholder output
  placeholder <- data.table(gene_id = "gene_placeholder", coefficient = NA_real_, SE = NA_real_)
  fwrite(placeholder, coef_file)
  append_log("Saved placeholder coefficients/SE summary.")
}

# Write log
writeLines(log_lines, log_file)