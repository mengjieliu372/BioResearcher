exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 4-dry-experiment-2: KEGG pathway analysis (placeholder if no DEG input)
# Constraints: only allowlisted inputs; graceful missing handling; output under /workspace/coding3

suppressPackageStartupMessages({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    install.packages("data.table")
  }
  library(data.table)
})

# Output paths (must be under /workspace/coding3)
out_kegg <- "/workspace/coding3/kegg_analysis_results.tsv"
out_log  <- "/workspace/coding3/part4_dry_experiment_2_log.txt"

log_lines <- c()
log_lines <- c(log_lines, paste0("Part 4-dry-experiment-2 started at: ", Sys.time()))

# NOTE:
# The task specifies using the same DEG data frame as GO analysis.
# Under the current strict allowlist, no DEG file is available.
# Therefore, create a placeholder KEGG output table.

log_lines <- c(log_lines, "No DEG input file available under the strict allowlist.")
log_lines <- c(log_lines, "Creating placeholder KEGG results table.")

# Placeholder KEGG results table (tab-delimited with required columns)
kegg_placeholder <- data.table(
  pathway_name = "NO_DEG_INPUT",
  gene_count   = 0L,
  adj_p_value  = NA_real_
)

# Write tab-delimited output
fwrite(kegg_placeholder, out_kegg, sep = "\t", quote = FALSE, na = "NA")

log_lines <- c(log_lines, paste0("KEGG results written to: ", out_kegg))
log_lines <- c(log_lines, paste0("Part 4-dry-experiment-2 completed at: ", Sys.time()))

# Write log
writeLines(log_lines, out_log)

# Print status
cat(paste(log_lines, collapse = "\n"), "\n")