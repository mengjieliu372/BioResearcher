exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 4-dry-experiment-2: KEGG pathway analysis
# Constraints: use only allowlisted inputs; handle missing files/packages gracefully.

set.seed(1)
options(stringsAsFactors = FALSE)

suppressWarnings({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    # data.table is listed as installed, but guard anyway
    install.packages("data.table", repos = "https://cloud.r-project.org")
  }
})

library(data.table)

log_path <- "/workspace/coding3/part4_dry_experiment_2_log.txt"
out_path <- "/workspace/coding3/kegg_analysis_results.tsv"

log_msg <- function(...) {
  cat(sprintf("[%s] ", Sys.time()), sprintf(...), "\n", file = log_path, append = TRUE)
}

log_msg("Part 4-dry-experiment-2 started.")

# Allowlisted input candidates (must be from the strict allowlist)
input_candidates <- c(
  "/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
  "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  "/workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz",
  "/workspace/data/GSE247026_Sample_genes_fpkm.xlsx",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz"
)

input_file <- input_candidates[file.exists(input_candidates)][1]

if (is.na(input_file) || !file.exists(input_file)) {
  log_msg("No allowlisted input file found. Writing placeholder KEGG results.")
  placeholder <- data.frame(
    pathway_name = "No_input_available",
    gene_count = 0,
    adj_p_value = NA_real_
  )
  fwrite(placeholder, out_path, sep = "\t", quote = FALSE, na = "NA")
  log_msg("KEGG results saved: %s (placeholder)", out_path)
} else {
  log_msg("Using input file: %s", input_file)

  # Read input depending on file type
  input_dt <- NULL
  if (grepl("\\.xlsx$", input_file, ignore.case = TRUE)) {
    if (!requireNamespace("readxl", quietly = TRUE)) {
      install.packages("readxl", repos = "https://cloud.r-project.org")
    }
    input_dt <- as.data.table(readxl::read_excel(input_file))
  } else {
    input_dt <- tryCatch({
      fread(input_file)
    }, error = function(e) {
      log_msg("Warning: failed to read input: %s", e$message)
      NULL
    })
  }

  if (is.null(input_dt) || nrow(input_dt) == 0) {
    log_msg("Input is empty or unreadable. Writing placeholder KEGG results.")
    placeholder <- data.frame(
      pathway_name = "No_usable_input",
      gene_count = 0,
      adj_p_value = NA_real_
    )
    fwrite(placeholder, out_path, sep = "\t", quote = FALSE, na = "NA")
    log_msg("KEGG results saved: %s (placeholder)", out_path)
  } else {
    # Identify gene ID column (heuristic)
    gene_col <- NULL
    col_lower <- tolower(names(input_dt))
    if ("gene" %in% col_lower) gene_col <- names(input_dt)[col_lower == "gene"][1]
    if (is.null(gene_col) && "gene_id" %in% col_lower) gene_col <- names(input_dt)[col_lower == "gene_id"][1]
    if (is.null(gene_col) && "genes" %in% col_lower) gene_col <- names(input_dt)[col_lower == "genes"][1]
    if (is.null(gene_col)) gene_col <- names(input_dt)[1]  # fallback to first column

    # Extract numeric expression matrix
    expr_dt <- input_dt[, setdiff(names(input_dt), gene_col), with = FALSE]
    expr_mat <- as.matrix(expr_dt)
    suppressWarnings(storage.mode(expr_mat) <- "numeric")

    # Compute variance and pick top genes as proxy "significant" set
    if (ncol(expr_mat) >= 2 && nrow(expr_mat) >= 10) {
      vars <- apply(expr_mat, 1, var, na.rm = TRUE)
      ord <- order(vars, decreasing = TRUE)
      top_n <- min(3000, length(ord))
      top_idx <- ord[1:top_n]
      gene_ids <- input_dt[[gene_col]][top_idx]
    } else {
      gene_ids <- input_dt[[gene_col]]
    }

    gene_ids <- unique(as.character(gene_ids))
    gene_ids <- gene_ids[!is.na(gene_ids) & nzchar(gene_ids)]

    # Attempt KEGG enrichment with clusterProfiler if available (install if missing)
    if (!requireNamespace("clusterProfiler", quietly = TRUE) ||
        !requireNamespace("org.Hs.eg.db", quietly = TRUE)) {

      # Try minimal install; if fails, proceed without KEGG
      if (!requireNamespace("BiocManager", quietly = TRUE)) {
        try(install.packages("BiocManager", repos = "https://cloud.r-project.org"), silent = TRUE)
      }
      try(BiocManager::install(c("clusterProfiler", "org.Hs.eg.db"), update = FALSE, ask = FALSE), silent = TRUE)
    }

    if (requireNamespace("clusterProfiler", quietly = TRUE) &&
        requireNamespace("org.Hs.eg.db", quietly = TRUE)) {

      # Guess gene ID type and map to Entrez
      gene_ids_clean <- gene_ids
      if (any(grepl("^ENSG", gene_ids_clean))) {
        gene_ids_clean <- sub("\\..*$", "", gene_ids_clean)
        id_from <- "ENSEMBL"
      } else {
        id_from <- "SYMBOL"
      }

      mapped <- tryCatch({
        clusterProfiler::bitr(
          gene_ids_clean,
          fromType = id_from,
          toType = "ENTREZID",
          OrgDb = org.Hs.eg.db::org.Hs.eg.db
        )
      }, error = function(e) {
        log_msg("Mapping error: %s", e$message)
        NULL
      })

      if (!is.null(mapped) && nrow(mapped) > 0) {
        entrez_ids <- unique(mapped$ENTREZID)

        kegg_res <- tryCatch({
          clusterProfiler::enrichKEGG(
            gene = entrez_ids,
            organism = "hsa",
            pvalueCutoff = 0.05
          )
        }, error = function(e) {
          log_msg("KEGG enrichment error: %s", e$message)
          NULL
        })

        if (!is.null(kegg_res) && nrow(as.data.frame(kegg_res)) > 0) {
          kegg_df <- as.data.frame(kegg_res)
          out_df <- data.frame(
            pathway_name = kegg_df$Description,
            gene_count = kegg_df$Count,
            adj_p_value = kegg_df$p.adjust
          )
          fwrite(out_df, out_path, sep = "\t", quote = FALSE, na = "NA")
          log_msg("KEGG results saved: %s (n=%d)", out_path, nrow(out_df))
        } else {
          log_msg("KEGG enrichment returned no terms. Writing placeholder.")
          placeholder <- data.frame(
            pathway_name = "No_terms_passed_cutoff",
            gene_count = length(entrez_ids),
            adj_p_value = NA_real_
          )
          fwrite(placeholder, out_path, sep = "\t", quote = FALSE, na = "NA")
          log_msg("KEGG results saved: %s (placeholder)", out_path)
        }
      } else {
        log_msg("No Entrez mapping available. Writing placeholder.")
        placeholder <- data.frame(
          pathway_name = "No_mapped_genes",
          gene_count = 0,
          adj_p_value = NA_real_
        )
        fwrite(placeholder, out_path, sep = "\t", quote = FALSE, na = "NA")
        log_msg("KEGG results saved: %s (placeholder)", out_path)
      }
    } else {
      log_msg("clusterProfiler/org.Hs.eg.db unavailable. Writing placeholder.")
      placeholder <- data.frame(
        pathway_name = "KEGG_unavailable",
        gene_count = length(gene_ids),
        adj_p_value = NA_real_
      )
      fwrite(placeholder, out_path, sep = "\t", quote = FALSE, na = "NA")
      log_msg("KEGG results saved: %s (placeholder)", out_path)
    }
  }
}

log_msg("Part 4-dry-experiment-2 completed.")