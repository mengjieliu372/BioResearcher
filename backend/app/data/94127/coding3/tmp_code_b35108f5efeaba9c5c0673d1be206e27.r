exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part5-dry-experiment-4: Predictive modeling of lncRNAs for immunotherapy response
# Constraints: use ONLY allowlisted inputs; handle missing files gracefully; write outputs to /workspace/coding3

set.seed(1)
options(stringsAsFactors = FALSE)

suppressPackageStartupMessages({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    install.packages("data.table", repos = "https://cloud.r-project.org")
  }
  library(data.table)
  if (!requireNamespace("readxl", quietly = TRUE)) {
    install.packages("readxl", repos = "https://cloud.r-project.org")
  }
  library(readxl)
})

log_file <- "/workspace/coding3/part5_dry_experiment_4_log.txt"
out_file <- "/workspace/coding3/part5_dry_experiment_4_logistic_models.csv"

log_msg <- function(...) {
  msg <- paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", paste0(..., collapse = ""))
  cat(msg, "\n")
  cat(msg, "\n", file = log_file, append = TRUE)
}

log_msg("Part 5-dry-experiment-4 started.")

# Allowlisted input files
input_files <- list(
  gse202361_tpm = "/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
  gse247026_fpkm = "/workspace/data/GSE247026_Sample_genes_fpkm.xlsx",
  gse202361_counts = "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  gse168205_counts = "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  gse213065_tpm = "/workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz",
  gse91061_rld = "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz",
  gse91061_fpkm = "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv.gz",
  gse230773_counts = "/workspace/data/GSE230773_Read_counts.xlsx"
)

# Helper: load expression matrix from allowed inputs
load_expression <- function() {
  # Priority order: TPM then FPKM/Counts as fallback
  if (file.exists(input_files$gse202361_tpm)) {
    log_msg("Loading expression from: ", input_files$gse202361_tpm)
    dt <- data.table::fread(input_files$gse202361_tpm)
    return(dt)
  }
  if (file.exists(input_files$gse247026_fpkm)) {
    log_msg("Loading expression from: ", input_files$gse247026_fpkm)
    dt <- as.data.table(readxl::read_xlsx(input_files$gse247026_fpkm))
    return(dt)
  }
  if (file.exists(input_files$gse213065_tpm)) {
    log_msg("Loading expression from: ", input_files$gse213065_tpm)
    dt <- data.table::fread(input_files$gse213065_tpm)
    return(dt)
  }
  if (file.exists(input_files$gse91061_fpkm)) {
    log_msg("Loading expression from: ", input_files$gse91061_fpkm)
    dt <- data.table::fread(input_files$gse91061_fpkm)
    return(dt)
  }
  if (file.exists(input_files$gse91061_rld)) {
    log_msg("Loading expression from: ", input_files$gse91061_rld)
    dt <- data.table::fread(input_files$gse91061_rld)
    return(dt)
  }
  if (file.exists(input_files$gse202361_counts)) {
    log_msg("Loading expression from: ", input_files$gse202361_counts)
    dt <- data.table::fread(input_files$gse202361_counts)
    return(dt)
  }
  if (file.exists(input_files$gse168205_counts)) {
    log_msg("Loading expression from: ", input_files$gse168205_counts)
    dt <- data.table::fread(input_files$gse168205_counts)
    return(dt)
  }
  if (file.exists(input_files$gse230773_counts)) {
    log_msg("Loading expression from: ", input_files$gse230773_counts)
    dt <- as.data.table(readxl::read_xlsx(input_files$gse230773_counts))
    return(dt)
  }
  return(NULL)
}

expr_dt <- load_expression()

if (is.null(expr_dt) || nrow(expr_dt) == 0) {
  log_msg("WARNING: No usable expression file found. Writing placeholder output.")
  placeholder <- data.table(
    lncRNA = NA_character_,
    odds_ratio = NA_real_,
    ci_lower = NA_real_,
    ci_upper = NA_real_,
    p_value = NA_real_,
    response_definition = "missing_expression_data",
    note = "No expression matrix available from allowlisted inputs."
  )
  data.table::fwrite(placeholder, out_file)
  log_msg("Placeholder output saved: ", out_file)
  log_msg("Part 5-dry-experiment-4 completed with placeholder.")
  quit(save = "no")
}

# Determine gene column (first non-numeric column)
gene_col <- NULL
for (col in names(expr_dt)) {
  if (!is.numeric(expr_dt[[col]])) {
    gene_col <- col
    break
  }
}
if (is.null(gene_col)) {
  # Assume rownames are genes; create synthetic gene IDs
  expr_dt[, gene_id := paste0("Gene_", seq_len(nrow(expr_dt)))]
  gene_col <- "gene_id"
  log_msg("WARNING: No non-numeric gene column detected; created synthetic gene IDs.")
}

# Move gene column to rownames-like vector
genes <- as.character(expr_dt[[gene_col]])
expr_dt[[gene_col]] <- NULL

# Keep only numeric columns
num_cols <- names(expr_dt)[sapply(expr_dt, is.numeric)]
if (length(num_cols) < 2) {
  log_msg("WARNING: Not enough numeric sample columns. Writing placeholder output.")
  placeholder <- data.table(
    lncRNA = NA_character_,
    odds_ratio = NA_real_,
    ci_lower = NA_real_,
    ci_upper = NA_real_,
    p_value = NA_real_,
    response_definition = "insufficient_numeric_columns",
    note = "Expression matrix does not have enough sample columns."
  )
  data.table::fwrite(placeholder, out_file)
  log_msg("Placeholder output saved: ", out_file)
  log_msg("Part 5-dry-experiment-4 completed with placeholder.")
  quit(save = "no")
}

expr_mat <- as.matrix(expr_dt[, ..num_cols])
rownames(expr_mat) <- genes

# Identify lncRNAs by name pattern (proxy)
lnc_pattern <- paste(
  c("^LINC", "^MIR", "^SNHG", "^MEG3$", "^HOTAIR$", "^MALAT1$", "^NEAT1$"),
  collapse = "|"
)
lnc_idx <- grepl(lnc_pattern, rownames(expr_mat), ignore.case = FALSE)
lnc_genes <- rownames(expr_mat)[lnc_idx]

proxy_note <- NULL
if (length(lnc_genes) == 0) {
  # fallback to top-variance genes as proxy lncRNAs
  log_msg("WARNING: No lncRNA-like gene symbols detected; using top-variance genes as proxy.")
  v <- apply(expr_mat, 1, var, na.rm = TRUE)
  lnc_genes <- names(sort(v, decreasing = TRUE))[1:min(50, length(v))]
  proxy_note <- "proxy_lncRNA_top_variance"
}

# Build proxy response (if clinical response absent)
checkpoint_genes <- c("PDCD1","CD274","CTLA4","LAG3","HAVCR2","TIGIT")
present_ck <- intersect(checkpoint_genes, rownames(expr_mat))

if (length(present_ck) > 0) {
  ck_expr <- colMeans(expr_mat[present_ck, , drop = FALSE], na.rm = TRUE)
  response <- ifelse(ck_expr > median(ck_expr, na.rm = TRUE), 1, 0)
  response_def <- "proxy_response_median_checkpoint_expression"
  log_msg("Response defined using median checkpoint expression (proxy).")
} else {
  # fallback: library size median
  libsize <- colSums(expr_mat, na.rm = TRUE)
  response <- ifelse(libsize > median(libsize, na.rm = TRUE), 1, 0)
  response_def <- "proxy_response_median_library_size"
  log_msg("WARNING: Checkpoint genes not detected; using median library size as proxy response.")
}

# Prepare modeling data
lnc_mat <- t(expr_mat[lnc_genes, , drop = FALSE])
model_df <- as.data.frame(lnc_mat)
model_df$response <- as.factor(response)

# Fit univariate logistic regression for each lncRNA
results <- lapply(lnc_genes, function(g) {
  x <- model_df[[g]]
  # Guard against constant predictors
  if (length(unique(x[!is.na(x)])) < 2) {
    return(data.table(
      lncRNA = g,
      odds_ratio = NA_real_,
      ci_lower = NA_real_,
      ci_upper = NA_real_,
      p_value = NA_real_,
      response_definition = response_def,
      note = "constant_predictor"
    ))
  }
  fit <- glm(response ~ x, family = binomial)
  coef_est <- coef(summary(fit))
  if (!"x" %in% rownames(coef_est)) {
    return(data.table(
      lncRNA = g,
      odds_ratio = NA_real_,
      ci_lower = NA_real_,
      ci_upper = NA_real_,
      p_value = NA_real_,
      response_definition = response_def,
      note = "model_fit_issue"
    ))
  }
  beta <- coef_est["x", "Estimate"]
  se <- coef_est["x", "Std. Error"]
  pval <- coef_est["x", "Pr(>|z|)"]
  z <- qnorm(0.975)
  ci_low <- beta - z * se
  ci_high <- beta + z * se
  data.table(
    lncRNA = g,
    odds_ratio = exp(beta),
    ci_lower = exp(ci_low),
    ci_upper = exp(ci_high),
    p_value = pval,
    response_definition = response_def,
    note = ifelse(is.null(proxy_note), "", proxy_note)
  )
})

res_dt <- data.table::rbindlist(results, fill = TRUE)

# Save results
data.table::fwrite(res_dt, out_file)
log_msg("Logistic regression results saved: ", out_file)
log_msg("Rows written: ", nrow(res_dt))
log_msg("Part 5-dry-experiment-4 completed.")