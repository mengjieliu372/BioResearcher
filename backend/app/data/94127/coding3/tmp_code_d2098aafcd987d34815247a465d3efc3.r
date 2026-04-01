exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 1-dry-experiment-6
# Record detailed characteristics of each selected sample in a structured format
# Inputs are restricted to the allowlisted files below.

suppressPackageStartupMessages({
  library(data.table)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Allowlisted input files
f_sample_meta <- "/workspace/data/GSE267611_sample_meta_out.txt.gz"
f_raw_counts  <- "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz"
f_cytolytic   <- "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"

# Helper to read files safely
safe_fread <- function(path, ...) {
  if (file.exists(path)) {
    tryCatch(
      fread(path, ...),
      error = function(e) {
        warning(sprintf("Failed to read %s: %s", path, e$message))
        data.table()
      }
    )
  } else {
    warning(sprintf("Missing file: %s", path))
    data.table()
  }
}

# Helper to find a column by regex
find_col <- function(dt, patterns) {
  if (ncol(dt) == 0) return(NA_character_)
  cn <- colnames(dt)
  hit <- cn[sapply(cn, function(x) any(grepl(patterns, x, ignore.case = TRUE)))]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
}

# Helper for first non-NA value
first_non_na <- function(x) {
  if (length(x) == 0) return(NA)
  y <- x[!is.na(x) & x != ""]
  if (length(y) == 0) return(NA)
  y[1]
}

schema_cols <- c("SampleID", "PatientAge", "Gender", "TumorGrade", "TumorStage", "CytolyticScore", "SourceFile")

# 1) Sample meta file
dt_meta <- safe_fread(f_sample_meta)
meta_out <- data.table()
if (nrow(dt_meta) > 0) {
  col_sample <- find_col(dt_meta, c("^sample", "sample_id", "geo", "gsm", "id$"))
  col_age    <- find_col(dt_meta, c("age"))
  col_gender <- find_col(dt_meta, c("gender", "sex"))
  col_grade  <- find_col(dt_meta, c("grade"))
  col_stage  <- find_col(dt_meta, c("stage"))

  if (is.na(col_sample)) {
    # fallback to first column
    col_sample <- colnames(dt_meta)[1]
  }

  meta_out <- data.table(
    SampleID       = as.character(dt_meta[[col_sample]]),
    PatientAge     = if (!is.na(col_age)) as.character(dt_meta[[col_age]]) else NA_character_,
    Gender         = if (!is.na(col_gender)) as.character(dt_meta[[col_gender]]) else NA_character_,
    TumorGrade     = if (!is.na(col_grade)) as.character(dt_meta[[col_grade]]) else NA_character_,
    TumorStage     = if (!is.na(col_stage)) as.character(dt_meta[[col_stage]]) else NA_character_,
    CytolyticScore = NA_character_,
    SourceFile     = basename(f_sample_meta)
  )
}

# 2) Raw counts file (genes x samples); use column names as Sample IDs
dt_raw <- safe_fread(f_raw_counts)
raw_out <- data.table()
if (nrow(dt_raw) > 0) {
  # assume first column is gene ID; others are sample columns
  sample_cols <- colnames(dt_raw)
  if (length(sample_cols) >= 2) {
    sample_ids <- sample_cols[-1]
    raw_out <- data.table(
      SampleID       = as.character(sample_ids),
      PatientAge     = NA_character_,
      Gender         = NA_character_,
      TumorGrade     = NA_character_,
      TumorStage     = NA_character_,
      CytolyticScore = NA_character_,
      SourceFile     = basename(f_raw_counts)
    )
  }
}

# 3) Cytolytic score file
dt_cyt <- safe_fread(f_cytolytic)
cyt_out <- data.table()
if (nrow(dt_cyt) > 0) {
  col_sample <- find_col(dt_cyt, c("^sample", "sample_id", "geo", "gsm", "id$"))
  col_score  <- find_col(dt_cyt, c("cytolytic", "score"))
  if (is.na(col_sample)) {
    col_sample <- colnames(dt_cyt)[1]
  }
  cyt_out <- data.table(
    SampleID       = as.character(dt_cyt[[col_sample]]),
    PatientAge     = NA_character_,
    Gender         = NA_character_,
    TumorGrade     = NA_character_,
    TumorStage     = NA_character_,
    CytolyticScore = if (!is.na(col_score)) as.character(dt_cyt[[col_score]]) else NA_character_,
    SourceFile     = basename(f_cytolytic)
  )
}

# Combine with shared schema
all_dt <- rbindlist(
  list(meta_out, raw_out, cyt_out),
  fill = TRUE
)

# If no data available, create placeholder
if (nrow(all_dt) == 0) {
  all_dt <- data.table(
    SampleID = NA_character_,
    PatientAge = NA_character_,
    Gender = NA_character_,
    TumorGrade = NA_character_,
    TumorStage = NA_character_,
    CytolyticScore = NA_character_,
    SourceFile = NA_character_
  )
}

# Deduplicate by SampleID and coalesce fields
final_dt <- all_dt[, .(
  PatientAge     = first_non_na(PatientAge),
  Gender         = first_non_na(Gender),
  TumorGrade     = first_non_na(TumorGrade),
  TumorStage     = first_non_na(TumorStage),
  CytolyticScore = first_non_na(CytolyticScore),
  SourceFile     = paste(unique(na.omit(SourceFile)), collapse = ";")
), by = SampleID]

# Save output
out_file <- file.path(out_dir, "sample_characteristics_detailed.csv")
fwrite(final_dt, out_file)

cat("Saved structured sample characteristics to:", out_file, "\n")