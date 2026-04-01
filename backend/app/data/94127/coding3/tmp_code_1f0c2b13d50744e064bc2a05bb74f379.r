exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 1-dry-experiment-7: Calculate summary statistics for collected samples
# Inputs are restricted to the allowlisted files only.

suppressPackageStartupMessages({
  library(data.table)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Allowlisted input files for this task
files <- c(
  meta = "/workspace/data/GSE267611_sample_meta_out.txt.gz",
  raw_counts = "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz",
  cytolytic = "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"
)

# Helper to safely read files
safe_fread <- function(path, ...) {
  if (!file.exists(path)) {
    warning(sprintf("Missing file: %s. Using empty placeholder.", path))
    return(data.table())
  }
  tryCatch(
    fread(path, ...),
    error = function(e) {
      warning(sprintf("Failed to read %s: %s. Using empty placeholder.", path, e$message))
      data.table()
    }
  )
}

# Helper to parse numeric age from mixed strings
parse_age <- function(x) {
  if (is.null(x)) return(rep(NA_real_, 0))
  x <- as.character(x)
  x <- gsub("[^0-9.]", "", x)
  suppressWarnings(as.numeric(x))
}

# Extract standardized sample metadata from meta file
extract_from_meta <- function(dt, source_file) {
  if (nrow(dt) == 0) {
    return(data.table(sample_id = character(), age = numeric(), gender = character(),
                      grade = character(), stage = character(), source_file = character()))
  }
  nms <- tolower(names(dt))

  # Identify columns
  sample_col <- names(dt)[grepl("sample|geo_accession|gsm|id", nms)][1]
  age_col    <- names(dt)[grepl("^age$|age", nms)][1]
  gender_col <- names(dt)[grepl("gender|sex", nms)][1]
  grade_col  <- names(dt)[grepl("grade", nms)][1]
  stage_col  <- names(dt)[grepl("stage|staging", nms)][1]

  # Fallback if no explicit sample_id column
  if (is.na(sample_col) || length(sample_col) == 0) {
    sample_ids <- if (!is.null(rownames(dt)) && any(rownames(dt) != "")) rownames(dt) else as.character(seq_len(nrow(dt)))
  } else {
    sample_ids <- as.character(dt[[sample_col]])
  }

  data.table(
    sample_id  = sample_ids,
    age        = if (!is.na(age_col)) parse_age(dt[[age_col]]) else NA_real_,
    gender     = if (!is.na(gender_col)) as.character(dt[[gender_col]]) else NA_character_,
    grade      = if (!is.na(grade_col)) as.character(dt[[grade_col]]) else NA_character_,
    stage      = if (!is.na(stage_col)) as.character(dt[[stage_col]]) else NA_character_,
    source_file = source_file
  )
}

# Extract placeholder metadata from expression-like tables (use column names as sample IDs)
extract_from_expression <- function(dt, source_file) {
  if (nrow(dt) == 0) {
    return(data.table(sample_id = character(), age = numeric(), gender = character(),
                      grade = character(), stage = character(), source_file = character()))
  }
  # Assume first column is feature/gene and remaining columns are samples
  sample_ids <- setdiff(names(dt), names(dt)[1])
  if (length(sample_ids) == 0) {
    sample_ids <- names(dt)  # fallback
  }
  data.table(
    sample_id = sample_ids,
    age = NA_real_,
    gender = NA_character_,
    grade = NA_character_,
    stage = NA_character_,
    source_file = source_file
  )
}

# Read inputs
dt_meta <- safe_fread(files["meta"])
dt_raw  <- safe_fread(files["raw_counts"])
dt_cyt  <- safe_fread(files["cytolytic"])

# Standardize to shared schema
meta_tbl <- extract_from_meta(dt_meta, files["meta"])
raw_tbl  <- extract_from_expression(dt_raw, files["raw_counts"])

# Cytolytic score file: try to detect sample_id column, else first column
cyt_tbl <- if (nrow(dt_cyt) == 0) {
  data.table(sample_id = character(), age = numeric(), gender = character(),
             grade = character(), stage = character(), source_file = character())
} else {
  nms <- tolower(names(dt_cyt))
  sample_col <- names(dt_cyt)[grepl("sample|id|gsm", nms)][1]
  sample_ids <- if (!is.na(sample_col) && length(sample_col) > 0) {
    as.character(dt_cyt[[sample_col]])
  } else {
    as.character(dt_cyt[[1]])
  }
  data.table(
    sample_id = sample_ids,
    age = NA_real_,
    gender = NA_character_,
    grade = NA_character_,
    stage = NA_character_,
    source_file = files["cytolytic"]
  )
}

# Combine all standardized tables
combined <- rbindlist(list(meta_tbl, raw_tbl, cyt_tbl), fill = TRUE)

# Summary statistics
ages <- combined$age
ages <- ages[!is.na(ages)]

mean_age   <- if (length(ages) > 0) mean(ages) else NA_real_
median_age <- if (length(ages) > 0) median(ages) else NA_real_

# Mode function
mode_value <- function(x) {
  if (length(x) == 0) return(NA_real_)
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}
mode_age <- if (length(ages) > 0) mode_value(ages) else NA_real_

age_stats <- data.table(
  section = "age_stats",
  variable = "age",
  level = c("mean", "median", "mode"),
  value = c(mean_age, median_age, mode_age)
)

# Frequency counts for gender, grade, stage
freq_table <- function(vec, varname) {
  vec <- as.character(vec)
  vec <- vec[!is.na(vec) & vec != ""]
  if (length(vec) == 0) {
    return(data.table(section = "frequency", variable = varname, level = NA_character_, value = 0))
  }
  tab <- table(vec)
  data.table(
    section = "frequency",
    variable = varname,
    level = names(tab),
    value = as.integer(tab)
  )
}

freq_gender <- freq_table(combined$gender, "gender")
freq_grade  <- freq_table(combined$grade, "grade")
freq_stage  <- freq_table(combined$stage, "stage")

summary_report <- rbindlist(list(age_stats, freq_gender, freq_grade, freq_stage), fill = TRUE)

# Save summary statistics report
out_file <- file.path(out_dir, "sample_statistics_summary.csv")
fwrite(summary_report, out_file)

message(sprintf("Summary statistics saved to: %s", out_file))