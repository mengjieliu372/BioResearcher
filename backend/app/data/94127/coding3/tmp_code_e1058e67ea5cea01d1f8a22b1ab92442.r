exit <- function(code=0) quit(status=as.integer(code), save='no')
# Task: Part 1-dry-experiment-2
# Query TCGA for liposarcoma cases (offline placeholder using allowed local files)

suppressPackageStartupMessages({
  library(data.table)
})

# Define inputs (allowlist)
input_files <- c(
  "/workspace/data/GSE267611_sample_meta_out.txt.gz",
  "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz",
  "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"
)

# Output directory and file
out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
out_file <- file.path(out_dir, "tcga_liposarcoma_cases.csv")

# Helper: safe fread with fallback
safe_fread <- function(f, nrows = NULL) {
  if (!file.exists(f)) {
    warning(sprintf("Missing file: %s", f))
    return(NULL)
  }
  dt <- tryCatch(
    {
      if (is.null(nrows)) fread(f, data.table = TRUE) else fread(f, nrows = nrows, data.table = TRUE)
    },
    error = function(e) {
      warning(sprintf("Failed to read %s: %s", f, e$message))
      return(NULL)
    }
  )
  return(dt)
}

# Helper: standardize schema
standardize_schema <- function(dt, source_file) {
  if (is.null(dt) || nrow(dt) == 0) return(NULL)
  # Identify potential sample ID column
  id_candidates <- c("sample_id", "Sample", "SAMPLE", "GSM", "geo_accession", "SampleID")
  id_col <- intersect(id_candidates, names(dt))
  sample_id <- if (length(id_col) > 0) dt[[id_col[1]]] else seq_len(nrow(dt))
  
  # Create a combined metadata text for filtering
  char_cols <- names(dt)[sapply(dt, is.character)]
  combined_text <- if (length(char_cols) > 0) {
    apply(dt[, ..char_cols], 1, function(x) paste(x, collapse = " "))
  } else {
    rep("", nrow(dt))
  }
  
  out <- data.table(
    sample_id = as.character(sample_id),
    clinical_data = combined_text,
    metadata = combined_text,
    tumor_characteristics = combined_text,
    source_file = basename(source_file)
  )
  return(out)
}

# Read and process inputs
dt_list <- list()
for (f in input_files) {
  # Read minimal rows for large tables to avoid heavy memory usage
  nrows <- if (grepl("raw.csv.gz", f, fixed = TRUE)) 50 else NULL
  dt <- safe_fread(f, nrows = nrows)
  if (!is.null(dt)) {
    std_dt <- standardize_schema(dt, f)
    if (!is.null(std_dt)) dt_list[[length(dt_list) + 1]] <- std_dt
  }
}

# Combine with shared schema
combined <- if (length(dt_list) > 0) {
  rbindlist(dt_list, fill = TRUE)
} else {
  data.table(sample_id = character(),
             clinical_data = character(),
             metadata = character(),
             tumor_characteristics = character(),
             source_file = character())
}

# Filter for liposarcoma keyword (case-insensitive)
liposarcoma_cases <- combined[
  grepl("lipo", clinical_data, ignore.case = TRUE) |
  grepl("lipo", metadata, ignore.case = TRUE) |
  grepl("lipo", tumor_characteristics, ignore.case = TRUE)
]

# If no cases found, create placeholder
if (nrow(liposarcoma_cases) == 0) {
  liposarcoma_cases <- data.table(
    sample_id = NA_character_,
    clinical_data = NA_character_,
    metadata = NA_character_,
    tumor_characteristics = NA_character_,
    source_file = NA_character_,
    note = "No liposarcoma cases detected in local allowlisted files. TCGA API access not available in this environment.",
    query_filter = "Liposarcoma"
  )
} else {
  liposarcoma_cases[, `:=`(
    note = "Derived from local allowlisted files; TCGA API not accessed.",
    query_filter = "Liposarcoma"
  )]
}

# Save output
fwrite(liposarcoma_cases, out_file)

message(sprintf("Saved liposarcoma cases dataset to: %s", out_file))