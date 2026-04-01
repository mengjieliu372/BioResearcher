exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 1-dry-experiment-4: Document unique sample IDs from local biobank databases
# Inputs (allowlisted):
# - /workspace/data/GSE267611_sample_meta_out.txt.gz
# - /workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz
# - /workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz

suppressPackageStartupMessages({
  library(data.table)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# Helper to safely read gz/txt/csv
safe_fread <- function(path, ...) {
  if (!file.exists(path)) {
    warning(sprintf("Missing file: %s. Returning empty data.table.", path))
    return(data.table())
  }
  res <- tryCatch(
    fread(path, ...),
    error = function(e) {
      warning(sprintf("Failed to read %s: %s. Returning empty data.table.", path, e$message))
      data.table()
    }
  )
  return(res)
}

# Helper to standardize schema
standardize_schema <- function(dt, source_file, sample_id_col = NULL) {
  if (nrow(dt) == 0) {
    return(data.table(
      sample_id = character(),
      age = NA_character_,
      gender = NA_character_,
      diagnosis_date = NA_character_,
      source_file = source_file
    ))
  }
  
  # Identify sample_id column
  if (is.null(sample_id_col)) {
    id_candidates <- names(dt)[grepl("sample|id", names(dt), ignore.case = TRUE)]
    if (length(id_candidates) > 0) {
      sample_id_col <- id_candidates[1]
    } else {
      sample_id_col <- names(dt)[1]
    }
  }
  
  # Identify metadata columns if present
  age_col <- names(dt)[grepl("age", names(dt), ignore.case = TRUE)]
  gender_col <- names(dt)[grepl("gender|sex", names(dt), ignore.case = TRUE)]
  dx_col <- names(dt)[grepl("diagnosis|dx.*date|date", names(dt), ignore.case = TRUE)]
  
  out <- data.table(
    sample_id = as.character(dt[[sample_id_col]]),
    age = if (length(age_col) > 0) as.character(dt[[age_col[1]]]) else NA_character_,
    gender = if (length(gender_col) > 0) as.character(dt[[gender_col[1]]]) else NA_character_,
    diagnosis_date = if (length(dx_col) > 0) as.character(dt[[dx_col[1]]]) else NA_character_,
    source_file = source_file
  )
  
  return(out)
}

# 1) GSE267611 sample metadata
file_meta <- "/workspace/data/GSE267611_sample_meta_out.txt.gz"
meta_dt <- safe_fread(file_meta)
meta_std <- standardize_schema(meta_dt, source_file = basename(file_meta))

# 2) GSE91061 raw counts: sample IDs are column names (excluding gene identifier)
file_raw <- "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz"
raw_dt <- safe_fread(file_raw)
raw_samples <- data.table()
if (nrow(raw_dt) > 0) {
  # identify gene column
  gene_cols <- names(raw_dt)[grepl("^gene|symbol|id$", names(raw_dt), ignore.case = TRUE)]
  sample_cols <- setdiff(names(raw_dt), gene_cols)
  if (length(sample_cols) == 0) {
    warning("No sample columns detected in raw counts file; creating empty sample list.")
  } else {
    raw_samples <- data.table(
      sample_id = sample_cols,
      age = NA_character_,
      gender = NA_character_,
      diagnosis_date = NA_character_,
      source_file = basename(file_raw)
    )
  }
} else {
  raw_samples <- data.table(
    sample_id = character(),
    age = NA_character_,
    gender = NA_character_,
    diagnosis_date = NA_character_,
    source_file = basename(file_raw)
  )
}

# 3) Cytolytic score file: typically sample ID in first column
file_cyto <- "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"
cyto_dt <- safe_fread(file_cyto)
cyto_std <- standardize_schema(cyto_dt, source_file = basename(file_cyto))

# Combine and deduplicate
all_samples <- rbindlist(list(meta_std, raw_samples, cyto_std), fill = TRUE)
all_samples <- all_samples[!is.na(sample_id) & sample_id != ""]
unique_samples <- unique(all_samples, by = "sample_id")

# Save output
out_file <- file.path(out_dir, "biobank_unique_sample_ids.csv")
fwrite(unique_samples, out_file)

cat(sprintf("Saved unique biobank sample IDs to: %s\n", out_file))
cat(sprintf("Total unique samples: %d\n", nrow(unique_samples)))