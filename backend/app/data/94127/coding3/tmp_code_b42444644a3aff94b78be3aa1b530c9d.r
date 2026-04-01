exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-2: Create a design matrix for differential expression analysis using Limma
# Constraints honored: only allowlisted inputs, graceful handling for missing files, outputs under /workspace/coding3

suppressPackageStartupMessages({
  library(data.table)
  library(readxl)
  library(limma)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Allowlisted input files for this task (do not scan directories)
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

# Helper: read expression file to get sample names
read_expression_for_samples <- function(fpath) {
  if (!file.exists(fpath)) return(NULL)
  ext <- tools::file_ext(fpath)
  # For gz files, ext may be "gz"; infer by filename
  if (grepl("\\.xlsx$", fpath, ignore.case = TRUE)) {
    df <- tryCatch(readxl::read_excel(fpath), error = function(e) NULL)
  } else {
    df <- tryCatch(data.table::fread(fpath, data.table = FALSE), error = function(e) NULL)
  }
  if (is.null(df) || ncol(df) < 2) return(NULL)
  # Assume first column is gene/feature, remaining are samples
  sample_names <- colnames(df)[-1]
  list(samples = sample_names, file = fpath)
}

# Choose the first available input
selected <- NULL
for (f in input_files) {
  selected <- read_expression_for_samples(f)
  if (!is.null(selected)) break
}

# Create group assignments
if (is.null(selected)) {
  warning("No input files available from allowlist. Creating placeholder design matrix.")
  sample_names <- c("Sample1", "Sample2")
  group <- factor(c("Control", "Treatment"))
} else {
  sample_names <- selected$samples
  if (length(sample_names) < 2) {
    warning("Insufficient sample columns detected. Creating placeholder design matrix.")
    sample_names <- c("Sample1", "Sample2")
    group <- factor(c("Control", "Treatment"))
  } else {
    # Heuristic grouping based on sample names
    sn_lower <- tolower(sample_names)
    is_control <- grepl("control|normal|ctrl", sn_lower)
    is_treat   <- grepl("treat|treated|tumor|case|disease", sn_lower)
    group <- rep(NA_character_, length(sample_names))
    group[is_control] <- "Control"
    group[is_treat]   <- "Treatment"
    # Fill remaining by splitting in half if no labels
    if (all(is.na(group))) {
      half <- floor(length(sample_names)/2)
      group <- c(rep("Control", half), rep("Treatment", length(sample_names) - half))
    } else {
      # Replace any NA with the most common label or "Control"
      if (any(is.na(group))) {
        common <- names(sort(table(group), decreasing = TRUE))[1]
        common <- ifelse(is.na(common), "Control", common)
        group[is.na(group)] <- common
      }
    }
    group <- factor(group)
  }
}

# Build design matrix using limma
design_matrix <- model.matrix(~ 0 + group)
colnames(design_matrix) <- levels(group)
rownames(design_matrix) <- sample_names

# Save outputs
design_csv <- file.path(out_dir, "design_matrix.csv")
write.csv(design_matrix, design_csv, row.names = TRUE)

design_rds <- file.path(out_dir, "design_matrix.rds")
saveRDS(design_matrix, design_rds)

# Log file to capture which input was used
log_path <- file.path(out_dir, "design_matrix_log.txt")
log_lines <- c(
  paste("Selected input file:", ifelse(is.null(selected), "None (placeholder used)", selected$file)),
  paste("Number of samples:", nrow(design_matrix)),
  paste("Group levels:", paste(colnames(design_matrix), collapse = ", "))
)
writeLines(log_lines, log_path)

message("Design matrix created and saved to: ", design_csv)
message("RDS saved to: ", design_rds)
message("Log saved to: ", log_path)