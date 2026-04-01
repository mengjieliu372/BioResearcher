exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 2-dry-experiment-3: Normalize RNA-seq data using DESeq2 and gcRMA
# Constraints honored: only allowlisted inputs; graceful missing handling; outputs under /workspace/coding3

suppressPackageStartupMessages({
  library(data.table)
  library(DESeq2)
  library(readxl)
  library(gcrma)
  library(affy)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Allowlisted input files for this task
input_files <- c(
  "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz",
  "/workspace/data/GSE168205_annotated_combined.counts.txt.gz",
  "/workspace/data/GSE230773_Read_counts.xlsx",
  "/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
  "/workspace/data/GSE247026_Sample_genes_fpkm.xlsx",
  "/workspace/data/GSE55465_non-normalized_INT-B.txt.gz",
  "/workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz"
)

# Helper: read counts-like tables safely
read_counts_table <- function(path) {
  if (!file.exists(path)) {
    warning(sprintf("Missing file: %s", path))
    return(NULL)
  }
  ext <- tools::file_ext(path)
  dat <- NULL
  tryCatch({
    if (ext %in% c("gz", "txt", "csv")) {
      # fread can handle .gz
      dat <- data.table::fread(path, data.table = FALSE)
    } else if (ext %in% c("xlsx", "xls")) {
      dat <- as.data.frame(readxl::read_excel(path))
    } else {
      warning(sprintf("Unsupported extension for %s", path))
      dat <- NULL
    }
  }, error = function(e) {
    warning(sprintf("Failed to read %s: %s", path, e$message))
    dat <<- NULL
  })
  dat
}

# Helper: identify gene column
get_gene_col <- function(df) {
  gene_candidates <- c("gene", "gene_id", "genes", "Gene", "GeneID", "GENE", "id", "ID")
  gc <- intersect(gene_candidates, colnames(df))
  if (length(gc) > 0) return(gc[1])
  return(colnames(df)[1])
}

# Helper: extract numeric count matrix
extract_counts <- function(df) {
  gene_col <- get_gene_col(df)
  genes <- df[[gene_col]]
  # remove non-unique/NA genes
  genes <- as.character(genes)
  df <- df[, setdiff(colnames(df), gene_col), drop = FALSE]
  # keep numeric columns
  num_cols <- vapply(df, is.numeric, logical(1))
  df_num <- df[, num_cols, drop = FALSE]
  if (ncol(df_num) == 0) return(NULL)
  mat <- as.matrix(df_num)
  rownames(mat) <- genes
  mat
}

# Collect DESeq2 normalized counts across datasets (long format)
normalized_list <- list()

for (path in input_files) {
  # Only use raw counts-like files for DESeq2
  # Heuristic: skip TPM/FPKM/RLD files
  if (grepl("TPM|FPKM|rld", basename(path), ignore.case = TRUE)) next
  
  message("Processing for DESeq2: ", path)
  df <- read_counts_table(path)
  if (is.null(df)) {
    normalized_list[[basename(path)]] <- data.table(
      dataset = basename(path),
      gene_id = NA_character_,
      sample = NA_character_,
      normalized_count = NA_real_,
      note = "Missing or unreadable input"
    )
    next
  }
  
  counts <- extract_counts(df)
  if (is.null(counts)) {
    normalized_list[[basename(path)]] <- data.table(
      dataset = basename(path),
      gene_id = NA_character_,
      sample = NA_character_,
      normalized_count = NA_real_,
      note = "No numeric count columns detected"
    )
    next
  }
  
  # Clean counts for DESeq2
  counts[is.na(counts)] <- 0
  counts[counts < 0] <- 0
  counts <- round(counts)
  
  # Ensure at least 2 samples
  if (ncol(counts) < 2) {
    normalized_list[[basename(path)]] <- data.table(
      dataset = basename(path),
      gene_id = rownames(counts),
      sample = colnames(counts),
      normalized_count = as.numeric(counts),
      note = "Insufficient samples for DESeq2; raw counts used"
    )
    next
  }
  
  # Run DESeq2 size factor normalization
  deseq_dt <- tryCatch({
    coldata <- data.frame(row.names = colnames(counts))
    dds <- DESeqDataSetFromMatrix(countData = counts, colData = coldata, design = ~1)
    dds <- estimateSizeFactors(dds)
    ncounts <- counts(dds, normalized = TRUE)
    # long format
    dt <- data.table::as.data.table(ncounts, keep.rownames = "gene_id")
    dt_long <- data.table::melt(dt, id.vars = "gene_id",
                               variable.name = "sample",
                               value.name = "normalized_count")
    dt_long[, dataset := basename(path)]
    dt_long[, note := NA_character_]
    dt_long
  }, error = function(e) {
    warning(sprintf("DESeq2 failed for %s: %s", path, e$message))
    data.table(
      dataset = basename(path),
      gene_id = NA_character_,
      sample = NA_character_,
      normalized_count = NA_real_,
      note = paste("DESeq2 failed:", e$message)
    )
  })
  
  normalized_list[[basename(path)]] <- deseq_dt
}

# Combine using rbindlist (fill=TRUE per constraints)
deseq2_normalized <- data.table::rbindlist(normalized_list, fill = TRUE)

# Save DESeq2 normalized counts
deseq2_outfile <- file.path(out_dir, "deseq2_normalized_counts.csv")
data.table::fwrite(deseq2_normalized, deseq2_outfile)

# --- gcRMA normalization ---
# gcRMA requires Affy CEL files (AffyBatch). None are allowlisted.
# We therefore write a placeholder output describing unavailability.
gcrma_outfile <- file.path(out_dir, "gcrma_normalized_expression.txt")

gcrma_placeholder <- data.table(
  message = "gcRMA normalization requires Affy CEL files (AffyBatch).",
  detail = "No CEL files are available in the allowlisted inputs for this task; gcRMA not performed."
)

data.table::fwrite(gcrma_placeholder, gcrma_outfile, sep = "\t")

message("DESeq2 normalized counts saved to: ", deseq2_outfile)
message("gcRMA placeholder output saved to: ", gcrma_outfile)