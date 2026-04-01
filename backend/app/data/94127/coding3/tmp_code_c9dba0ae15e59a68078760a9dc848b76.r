exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part5-dry-experiment-5: Document challenges faced during analysis
# Output: comprehensive challenges report with suggested solutions/adjustments

options(stringsAsFactors = FALSE)
set.seed(1)

suppressWarnings({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    install.packages("data.table", repos = "https://cloud.r-project.org")
  }
  library(data.table)
})

output_report <- "/workspace/coding3/part5_dry_experiment_5_challenges_report.md"
output_log <- "/workspace/coding3/part5_dry_experiment_5_log.txt"

log_msg <- function(msg) {
  cat(sprintf("[%s] %s\n", Sys.time(), msg), file = output_log, append = TRUE)
}

log_msg("Part5-dry-experiment-5 started.")

# ---- Define known input files (allowlisted only) ----
inputs <- list(
  qc_report = "/workspace/coding3/qc_report.txt",
  qc_metrics = "/workspace/coding3/qc_metrics.csv",
  qc_excluded = "/workspace/coding3/qc_excluded_samples.csv",
  degs = "/workspace/coding3/part3_dry_experiment_5_degs.csv",
  eBayes_log = "/workspace/coding3/part3_dry_experiment_4_ebayes_log.txt",
  limma_log = "/workspace/coding3/part3_dry_experiment_3_lmfit_log.txt",
  go_log = "/workspace/coding3/part4_dry_experiment_1_log.txt",
  kegg_log = "/workspace/coding3/part4_dry_experiment_2_log.txt",
  kegg_res = "/workspace/coding3/kegg_analysis_results.tsv",
  go_res = "/workspace/coding3/go_enrichment_results.csv",
  part2_log = "/workspace/coding3/part2_download_log.txt",
  part2_manifest = "/workspace/coding3/part2_download_manifest.csv",
  deseq2_norm = "/workspace/coding3/deseq2_normalized_counts.csv",
  design_log = "/workspace/coding3/design_matrix_log.txt",
  logistic_models = "/workspace/coding3/part5_dry_experiment_4_logistic_models.csv"
)

# ---- Helper: read log lines if file exists ----
safe_read_lines <- function(path) {
  if (file.exists(path)) {
    return(readLines(path, warn = FALSE))
  } else {
    return(character())
  }
}

# ---- Collect issues/warnings from logs ----
log_sources <- list(
  part2_log = inputs$part2_log,
  qc_report = inputs$qc_report,
  limma_log = inputs$limma_log,
  eBayes_log = inputs$eBayes_log,
  go_log = inputs$go_log,
  kegg_log = inputs$kegg_log,
  design_log = inputs$design_log
)

issue_rows <- list()
for (nm in names(log_sources)) {
  lines <- safe_read_lines(log_sources[[nm]])
  if (length(lines) > 0) {
    hits <- lines[grepl("warning|missing|placeholder|fallback|no usable|cannot|failed|NA", 
                        tolower(lines))]
    if (length(hits) > 0) {
      issue_rows[[nm]] <- data.table(
        source = nm,
        issue_line = hits
      )
    }
  }
}

issues_dt <- rbindlist(issue_rows, fill = TRUE)

# ---- Summarize data availability challenges ----
data_avail_notes <- c()
if (file.exists(inputs$part2_log)) {
  part2_lines <- safe_read_lines(inputs$part2_log)
  miss_lines <- part2_lines[grepl("MISSING", part2_lines)]
  if (length(miss_lines) > 0) {
    data_avail_notes <- c(data_avail_notes, 
                          sprintf("Some datasets were missing during staging: %s", 
                                  paste(miss_lines, collapse = "; ")))
  }
} else {
  data_avail_notes <- c(data_avail_notes, "Download log unavailable; could not verify dataset availability.")
}

# ---- Summarize QC challenges ----
qc_notes <- c()
if (file.exists(inputs$qc_excluded)) {
  qc_exc <- tryCatch(fread(inputs$qc_excluded), error = function(e) NULL)
  if (!is.null(qc_exc) && nrow(qc_exc) > 0) {
    qc_notes <- c(qc_notes, sprintf("QC excluded %d samples; see qc_excluded_samples.csv.", nrow(qc_exc)))
  } else {
    qc_notes <- c(qc_notes, "QC exclusion list present but empty or unreadable.")
  }
} else {
  qc_notes <- c(qc_notes, "QC exclusion list missing; QC filtering could not be fully audited.")
}

# ---- Summarize DEG/limma challenges ----
deg_notes <- c()
if (file.exists(inputs$degs)) {
  deg_dt <- tryCatch(fread(inputs$degs), error = function(e) NULL)
  if (!is.null(deg_dt)) {
    if (nrow(deg_dt) == 0) {
      deg_notes <- c(deg_notes, "DEG table is empty; likely due to missing or placeholder inputs.")
    } else {
      deg_notes <- c(deg_notes, sprintf("DEG table produced with %d rows.", nrow(deg_dt)))
    }
  } else {
    deg_notes <- c(deg_notes, "DEG table present but unreadable.")
  }
} else {
  deg_notes <- c(deg_notes, "DEG table missing; downstream analyses may have used proxies/placeholders.")
}

# ---- Summarize GO/KEGG challenges ----
enrich_notes <- c()
if (file.exists(inputs$go_res)) {
  go_dt <- tryCatch(fread(inputs$go_res), error = function(e) NULL)
  if (is.null(go_dt) || nrow(go_dt) == 0) {
    enrich_notes <- c(enrich_notes, "GO enrichment results empty or unreadable; placeholders may have been used.")
  } else {
    enrich_notes <- c(enrich_notes, sprintf("GO enrichment produced %d rows.", nrow(go_dt)))
  }
} else {
  enrich_notes <- c(enrich_notes, "GO enrichment results missing.")
}

if (file.exists(inputs$kegg_res)) {
  kegg_dt <- tryCatch(fread(inputs$kegg_res), error = function(e) NULL)
  if (is.null(kegg_dt) || nrow(kegg_dt) == 0) {
    enrich_notes <- c(enrich_notes, "KEGG enrichment results empty or unreadable.")
  } else {
    enrich_notes <- c(enrich_notes, sprintf("KEGG enrichment produced %d rows.", nrow(kegg_dt)))
  }
} else {
  enrich_notes <- c(enrich_notes, "KEGG enrichment results missing.")
}

# ---- Summarize predictive modeling challenges ----
model_notes <- c()
if (file.exists(inputs$logistic_models)) {
  model_dt <- tryCatch(fread(inputs$logistic_models), error = function(e) NULL)
  if (is.null(model_dt) || nrow(model_dt) == 0) {
    model_notes <- c(model_notes, "Predictive modeling output empty or unreadable; may reflect proxy modeling.")
  } else {
    model_notes <- c(model_notes, "Predictive modeling completed with proxy response due to missing labels (per prior logs).")
  }
} else {
  model_notes <- c(model_notes, "Predictive modeling output missing.")
}

# ---- Compile report text ----
report_lines <- c(
  "# Challenges and Adjustments Report (Part 5-dry-experiment-5)",
  "",
  "## Overview",
  "This report documents the main challenges encountered across the analysis pipeline,",
  "including data availability issues, QC filtering, differential expression limitations,",
  "enrichment constraints, and proxy modeling. Suggested adjustments are provided.",
  "",
  "## Data Availability Challenges",
  if (length(data_avail_notes) > 0) paste0("- ", data_avail_notes) else "- No data availability issues detected.",
  "",
  "## Quality Control Challenges",
  if (length(qc_notes) > 0) paste0("- ", qc_notes) else "- No QC issues detected.",
  "",
  "## Differential Expression Challenges",
  if (length(deg_notes) > 0) paste0("- ", deg_notes) else "- No DEG issues detected.",
  "",
  "## Enrichment Analysis Challenges",
  if (length(enrich_notes) > 0) paste0("- ", enrich_notes) else "- No enrichment issues detected.",
  "",
  "## Predictive/Survival Modeling Challenges",
  if (length(model_notes) > 0) paste0("- ", model_notes) else "- No modeling issues detected.",
  "",
  "## Extracted Log Warnings/Flags",
  if (nrow(issues_dt) > 0) {
    paste0("A total of ", nrow(issues_dt), " warning/issue lines were detected in logs.")
  } else {
    "No warning/issue lines detected in available logs."
  },
  "",
  "### Suggested Adjustments / Solutions",
  "- Ensure all required datasets are staged before analysis to avoid placeholder outputs.",
  "- Maintain a central data manifest and verify checksums or file sizes.",
  "- If DEGs are empty, revisit group definitions, filtering thresholds, or data normalization.",
  "- For enrichment, confirm gene ID mapping quality; if mapping rate is low, consider alternate ID types.",
  "- For modeling steps lacking outcome labels, document proxy definitions clearly and plan for label acquisition.",
  "",
  "## Notes",
  "This document is generated from available logs and outputs only. Missing files may reduce completeness."
)

# ---- Write report ----
writeLines(report_lines, con = output_report)

# ---- Save issues table (optional in log-only) ----
if (nrow(issues_dt) > 0) {
  issues_csv <- "/workspace/coding3/part5_dry_experiment_5_issues_extracted.csv"
  fwrite(issues_dt, issues_csv)
  log_msg(paste("Extracted issues saved:", issues_csv))
} else {
  log_msg("No issues extracted from logs.")
}

log_msg(paste("Challenges report saved:", output_report))
log_msg("Part5-dry-experiment-5 completed.")