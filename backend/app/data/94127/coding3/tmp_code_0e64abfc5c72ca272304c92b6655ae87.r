exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 4-dry-experiment-3: Discussion document for therapeutic targets (GO/KEGG context)
# Constraints honored: only allowlisted inputs used; graceful missing handling; outputs under /workspace/coding3

set.seed(1)
options(stringsAsFactors = FALSE)

suppressPackageStartupMessages({
  library(data.table)
})

log_lines <- character()
log_msg <- function(msg) {
  log_lines <<- c(log_lines, sprintf("[%s] %s", Sys.time(), msg))
}

# Allowlisted input(s)
input_tpm <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"
# Note: GSE205492 not in allowlist, so we will mention unavailability in the document.

# Output paths
out_doc <- "/workspace/coding3/part4_dry_experiment_3_discussion.md"
out_log <- "/workspace/coding3/part4_dry_experiment_3_log.txt"

log_msg("Part 4-dry-experiment-3 started.")
log_msg(paste("Allowlisted TPM input:", input_tpm))

proxy_genes <- data.frame()
tpm_status <- "missing_or_failed"

if (file.exists(input_tpm)) {
  log_msg("TPM file found; attempting to read for proxy gene selection.")
  tpm_dt <- tryCatch({
    fread(input_tpm, data.table = FALSE)
  }, error = function(e) {
    log_msg(paste("Warning: Failed to read TPM file:", e$message))
    NULL
  })
  
  if (!is.null(tpm_dt) && nrow(tpm_dt) > 0 && ncol(tpm_dt) > 1) {
    # Assume first column is gene ID
    gene_ids <- tpm_dt[[1]]
    expr_df <- tpm_dt[, -1, drop = FALSE]
    
    # Convert to numeric matrix safely
    expr_mat <- suppressWarnings(data.matrix(expr_df))
    if (nrow(expr_mat) == length(gene_ids)) {
      vars <- apply(expr_mat, 1, var, na.rm = TRUE)
      if (length(vars) > 0) {
        top_n <- min(20, length(vars))
        top_idx <- order(vars, decreasing = TRUE)[seq_len(top_n)]
        proxy_genes <- data.frame(
          gene_id = gene_ids[top_idx],
          variance = vars[top_idx],
          stringsAsFactors = FALSE
        )
        tpm_status <- "ok"
        log_msg(paste("Computed proxy genes from TPM; top N =", top_n))
      } else {
        log_msg("Warning: Variance computation yielded no results.")
      }
    } else {
      log_msg("Warning: Expression matrix rows do not match gene ID length.")
    }
  } else {
    log_msg("Warning: TPM input is empty or has insufficient columns.")
  }
} else {
  log_msg("Warning: TPM file not found in allowlist path.")
}

# Build a markdown table for proxy genes if available
proxy_table_md <- "No proxy gene list could be generated from GSE202361 TPM."
if (nrow(proxy_genes) > 0) {
  # Format variance for readability
  proxy_genes$variance <- signif(proxy_genes$variance, 4)
  proxy_table_md <- paste0(
    "| Gene ID | Variance (TPM) |\n",
    "|---|---|\n",
    paste0("| ", proxy_genes$gene_id, " | ", proxy_genes$variance, " |", collapse = "\n")
  )
}

# Compose discussion document
doc_lines <- c(
  "# Discussion: Potential Therapeutic Targets from GO/KEGG Context",
  "",
  "## Overview",
  "This document summarizes potential therapeutic targets and pathway implications for liposarcoma.",
  "Due to input constraints in this run, formal GO and KEGG enrichment results were **not available** as direct inputs.",
  "Instead, a **proxy gene list** was derived from the high‑variance genes in the GSE202361 TPM matrix to guide discussion.",
  "",
  "## Data Availability and Limitations",
  "- **GSE202361 TPM**: available and used to derive proxy target candidates.",
  "- **GSE205492**: referenced in the task description but **not available in the allowlisted inputs** for this run.",
  "- **GO/KEGG results**: not provided as inputs; therefore, no direct enrichment terms are reported here.",
  "",
  "## Proxy Candidate Targets (GSE202361 Variance‑Based)",
  "These genes show high variance across samples in GSE202361 TPM and are proposed as preliminary candidates for further review:",
  "",
  proxy_table_md,
  "",
  "## GO/KEGG Context (Placeholder)",
  "Formal GO/KEGG enrichment was not possible in this run due to unavailable inputs.",
  "In a full analysis, the following would be expected:",
  "- **GO Biological Processes**: cell cycle regulation, extracellular matrix remodeling, stress response, and immune modulation.",
  "- **KEGG Pathways**: PI3K‑AKT signaling, MAPK signaling, focal adhesion, and apoptosis (typical sarcoma‑related pathways).",
  "These are **generic expectations** and should be replaced with actual enriched terms once GO/KEGG results are provided.",
  "",
  "## Therapeutic Implications (Preliminary)",
  "1. **High‑variance genes** may indicate tumor heterogeneity and potential vulnerabilities.",
  "2. Genes with strong variance should be cross‑validated with differential expression and enriched pathway membership.",
  "3. Candidates should be prioritized for literature review and experimental validation.",
  "",
  "## Expected Outcomes for Liposarcoma Treatment Strategies",
  "- Identification of **pathway‑level vulnerabilities** that can inform targeted therapies.",
  "- Prioritization of **gene targets** for functional validation.",
  "- Development of **combination strategies** targeting both proliferative and microenvironmental pathways.",
  "",
  "## Literature References",
  "No literature references were provided in the allowlisted inputs. Please insert appropriate citations here.",
  "",
  "## Next Steps",
  "1. Integrate actual GO and KEGG enrichment outputs.",
  "2. Map proxy candidates to known liposarcoma driver genes.",
  "3. Validate target feasibility using independent datasets or experimental data."
)

# Write outputs
writeLines(doc_lines, out_doc)
log_msg(paste("Discussion document written to:", out_doc))

writeLines(log_lines, out_log)