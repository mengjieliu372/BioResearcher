exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 4-dry-experiment-1: GO enrichment analysis for GSE202361 DEGs
# Constraints: use only allowlisted inputs; graceful handling; output under /workspace/coding3

suppressPackageStartupMessages({
  library(data.table)
  library(readxl)
})

output_file <- "/workspace/coding3/go_enrichment_results.csv"
log_file <- "/workspace/coding3/part4_dry_experiment_1_log.txt"

# Allowlisted inputs for this task
input_files <- c(
  "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  "/workspace/data/GSE247026_Sample_genes_fpkm.xlsx",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv.gz",
  "/workspace/data/GSE230773_Read_counts.xlsx",
  "/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
  "/workspace/data/GSE55465_non-normalized_INT-B.txt.gz"
)

log_msgs <- c()
log_msgs <- c(log_msgs, paste0("Part 4-dry-experiment-1 started at: ", Sys.time()))

# Helper to read header/colnames only
get_colnames_safe <- function(f) {
  cn <- NULL
  tryCatch({
    if (grepl("\\.xlsx$", f, ignore.case = TRUE)) {
      tmp <- readxl::read_excel(f, n_max = 0)
      cn <- colnames(tmp)
    } else {
      tmp <- data.table::fread(f, nrows = 0, data.table = FALSE)
      cn <- colnames(tmp)
    }
  }, error = function(e) {
    log_msgs <<- c(log_msgs, paste0("Warning: Failed to read columns from ", f, " : ", e$message))
  })
  cn
}

# Attempt to detect a DEG table within allowlisted inputs
deg_df <- NULL
deg_source <- NA_character_

adjp_patterns <- c("^adj\\.?p", "adj\\.p\\.val", "padj", "fdr", "qval", "qvalue", "adj\\.p\\.value")
gene_patterns <- c("^gene$", "^genes$", "gene_id", "geneid", "symbol", "hgnc", "gene_name")

for (f in input_files) {
  if (!file.exists(f)) {
    log_msgs <- c(log_msgs, paste0("Notice: File not found (allowed list): ", f))
    next
  }
  cn <- get_colnames_safe(f)
  if (is.null(cn) || length(cn) == 0) next

  # detect adjusted p-value column
  adjp_col <- cn[grepl(paste(adjp_patterns, collapse = "|"), cn, ignore.case = TRUE)]
  if (length(adjp_col) == 0) {
    log_msgs <- c(log_msgs, paste0("No adjusted p-value column detected in: ", f))
    next
  }

  # If we reach here, try to read full file
  log_msgs <- c(log_msgs, paste0("Potential DEG-like table detected in: ", f, " with adj p column(s): ", paste(adjp_col, collapse = ",")))
  tryCatch({
    if (grepl("\\.xlsx$", f, ignore.case = TRUE)) {
      tmp <- readxl::read_excel(f)
      tmp <- as.data.frame(tmp)
    } else {
      tmp <- data.table::fread(f, data.table = FALSE)
    }
    # identify gene column
    gene_col <- colnames(tmp)[grepl(paste(gene_patterns, collapse = "|"), colnames(tmp), ignore.case = TRUE)]
    if (length(gene_col) == 0) gene_col <- colnames(tmp)[1]
    adjp_col <- adjp_col[1]

    tmp <- tmp[!is.na(tmp[[adjp_col]]), , drop = FALSE]
    tmp <- tmp[tmp[[adjp_col]] < 0.05, , drop = FALSE]

    if (nrow(tmp) > 0) {
      deg_df <- data.frame(
        gene_id = as.character(tmp[[gene_col]]),
        adj_p = as.numeric(tmp[[adjp_col]]),
        stringsAsFactors = FALSE
      )
      deg_source <- f
      break
    } else {
      log_msgs <- c(log_msgs, paste0("No significant DEGs (adj p < 0.05) found in: ", f))
    }
  }, error = function(e) {
    log_msgs <<- c(log_msgs, paste0("Warning: Failed to parse candidate DEG table in ", f, " : ", e$message))
  })
}

# Perform GO enrichment if possible
go_results <- NULL
if (!is.null(deg_df) && nrow(deg_df) > 0) {
  gene_ids <- unique(na.omit(deg_df$gene_id))
  if (length(gene_ids) == 0) {
    log_msgs <- c(log_msgs, "DEG table found but contains no valid gene identifiers.")
  } else {
    # Check if clusterProfiler + org.Hs.eg.db are available
    has_clusterprof <- requireNamespace("clusterProfiler", quietly = TRUE)
    has_orgdb <- requireNamespace("org.Hs.eg.db", quietly = TRUE)

    if (has_clusterprof && has_orgdb) {
      log_msgs <- c(log_msgs, paste0("Running GO enrichment using gene list from: ", deg_source))
      tryCatch({
        enrich <- clusterProfiler::enrichGO(
          gene = gene_ids,
          OrgDb = org.Hs.eg.db::org.Hs.eg.db,
          keyType = "SYMBOL",
          ont = "BP",
          pAdjustMethod = "BH",
          pvalueCutoff = 0.05,
          qvalueCutoff = 0.05,
          readable = TRUE
        )
        enrich_df <- as.data.frame(enrich)

        if (nrow(enrich_df) > 0) {
          go_results <- data.frame(
            GO_term = enrich_df$Description,
            gene_count = enrich_df$Count,
            adj_p_value = enrich_df$p.adjust,
            stringsAsFactors = FALSE
          )
        } else {
          log_msgs <- c(log_msgs, "GO enrichment returned 0 terms after filtering.")
        }
      }, error = function(e) {
        log_msgs <<- c(log_msgs, paste0("Warning: GO enrichment failed: ", e$message))
      })
    } else {
      log_msgs <- c(log_msgs, paste0(
        "GO enrichment not run because required packages are missing. ",
        "clusterProfiler installed: ", has_clusterprof,
        "; org.Hs.eg.db installed: ", has_orgdb
      ))
    }
  }
} else {
  log_msgs <- c(log_msgs, "No DEG table with adjusted p-values found in allowlisted inputs; producing placeholder output.")
}

# If GO results are not available, create placeholder
if (is.null(go_results)) {
  go_results <- data.frame(
    GO_term = NA_character_,
    gene_count = NA_integer_,
    adj_p_value = NA_real_,
    stringsAsFactors = FALSE
  )
}

# Write output
data.table::fwrite(go_results, output_file)

# Write log
log_msgs <- c(log_msgs, paste0("Output written to: ", output_file))
log_msgs <- c(log_msgs, paste0("Part 4-dry-experiment-1 finished at: ", Sys.time()))
writeLines(log_msgs, log_file)