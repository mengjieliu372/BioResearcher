exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 1-dry-experiment-5: Review collected samples against inclusion/exclusion criteria
# Inputs (allowlisted): 
# - /workspace/data/GSE267611_sample_meta_out.txt.gz
# - /workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz
# - /workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz
# Output:
# - /workspace/coding3/eligible_samples_final.csv

suppressPackageStartupMessages({
  library(data.table)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Helper: safe fread
safe_fread <- function(path, ...) {
  if (!file.exists(path)) {
    warning(sprintf("Missing file: %s. Returning NULL placeholder.", path))
    return(NULL)
  }
  tryCatch(
    fread(path, ...),
    error = function(e) {
      warning(sprintf("Failed to read %s: %s. Returning NULL placeholder.", path, e$message))
      return(NULL)
    }
  )
}

# 1) GSE267611 sample metadata
meta_path <- "/workspace/data/GSE267611_sample_meta_out.txt.gz"
gse267611 <- safe_fread(meta_path)

gse267611_dt <- NULL
if (!is.null(gse267611)) {
  # Identify sample ID column
  sample_id_col <- NULL
  cand_cols <- c("sample_id", "sample", "gsm", "geo_accession", "accession", "Sample", "GSM")
  for (cc in cand_cols) {
    if (cc %in% names(gse267611)) { sample_id_col <- cc; break }
  }
  if (is.null(sample_id_col)) {
    # fallback to first column
    sample_id_col <- names(gse267611)[1]
  }
  
  # Standardize
  gse267611_dt <- as.data.table(gse267611)
  gse267611_dt[, sample_id := as.character(get(sample_id_col))]
  gse267611_dt[, source := "GSE267611_sample_meta"]
  
  # Try to derive diagnosis and prior treatment if columns exist
  diag_cols <- names(gse267611_dt)[grepl("diagnos|disease|tumor|histolog|cancer", names(gse267611_dt), ignore.case = TRUE)]
  treat_cols <- names(gse267611_dt)[grepl("treat|therapy|chemo|radiat|drug", names(gse267611_dt), ignore.case = TRUE)]
  
  gse267611_dt[, diagnosis := if (length(diag_cols) > 0) {
    apply(.SD, 1, function(x) {
      y <- x[!is.na(x) & x != ""]
      if (length(y) == 0) NA_character_ else as.character(y[1])
    })
  } else NA_character_, .SDcols = diag_cols]
  
  gse267611_dt[, prior_treatment := if (length(treat_cols) > 0) {
    apply(.SD, 1, function(x) {
      y <- x[!is.na(x) & x != ""]
      if (length(y) == 0) NA else TRUE
    })
  } else NA, .SDcols = treat_cols]
  
  # Clinical completeness: count non-NA in metadata fields (exclude sample_id/source)
  exclude_cols <- c("sample_id", "source", sample_id_col)
  meta_cols <- setdiff(names(gse267611_dt), exclude_cols)
  gse267611_dt[, clinical_fields_count := if (length(meta_cols) > 0) {
    apply(.SD, 1, function(x) sum(!is.na(x) & x != ""))
  } else 0, .SDcols = meta_cols]
  
  gse267611_dt[, clinical_complete := clinical_fields_count >= 3]
  
  # Map to shared schema (keep a subset plus counters)
  gse267611_dt <- gse267611_dt[, .(sample_id, source, diagnosis, prior_treatment, clinical_complete, clinical_fields_count)]
} else {
  gse267611_dt <- data.table(sample_id = character(), source = character(), diagnosis = character(),
                             prior_treatment = logical(), clinical_complete = logical(), clinical_fields_count = integer())
}

# 2) GSE91061 raw counts: use column names as sample IDs
raw_counts_path <- "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz"
gse91061_raw <- safe_fread(raw_counts_path)

gse91061_raw_dt <- NULL
if (!is.null(gse91061_raw)) {
  # sample columns are likely all columns except the first (gene IDs)
  if (ncol(gse91061_raw) > 1) {
    sample_ids <- names(gse91061_raw)[-1]
  } else {
    sample_ids <- names(gse91061_raw)
  }
  gse91061_raw_dt <- data.table(
    sample_id = as.character(sample_ids),
    source = "GSE91061_raw_counts",
    diagnosis = NA_character_,
    prior_treatment = NA,
    clinical_complete = FALSE,
    clinical_fields_count = 0L
  )
} else {
  gse91061_raw_dt <- data.table(sample_id = character(), source = character(), diagnosis = character(),
                                prior_treatment = logical(), clinical_complete = logical(), clinical_fields_count = integer())
}

# 3) GSE91061 cytolytic score: use sample IDs column
cytolytic_path <- "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"
gse91061_cyto <- safe_fread(cytolytic_path)

gse91061_cyto_dt <- NULL
if (!is.null(gse91061_cyto)) {
  # Detect sample ID column
  sample_id_col <- NULL
  cand_cols <- c("sample_id", "sample", "gsm", "geo_accession", "accession", "Sample", "GSM")
  for (cc in cand_cols) {
    if (cc %in% names(gse91061_cyto)) { sample_id_col <- cc; break }
  }
  if (is.null(sample_id_col)) {
    sample_id_col <- names(gse91061_cyto)[1]
  }
  gse91061_cyto_dt <- data.table(
    sample_id = as.character(gse91061_cyto[[sample_id_col]]),
    source = "GSE91061_cytolytic_score",
    diagnosis = NA_character_,
    prior_treatment = NA,
    clinical_complete = FALSE,
    clinical_fields_count = 0L
  )
} else {
  gse91061_cyto_dt <- data.table(sample_id = character(), source = character(), diagnosis = character(),
                                 prior_treatment = logical(), clinical_complete = logical(), clinical_fields_count = integer())
}

# Combine all metadata using shared schema
combined_meta <- rbindlist(list(gse267611_dt, gse91061_raw_dt, gse91061_cyto_dt), fill = TRUE)

# If no data at all, create placeholder output
if (nrow(combined_meta) == 0) {
  warning("No sample metadata available from inputs. Writing placeholder output.")
  placeholder <- data.table(
    sample_id = character(),
    sources = character(),
    inclusion_status = character(),
    exclusion_reason = character()
  )
  fwrite(placeholder, file.path(out_dir, "eligible_samples_final.csv"))
} else {
  # Aggregate by sample_id
  combined_meta[, diagnosis_present := !is.na(diagnosis) & diagnosis != ""]
  combined_meta[, prior_treatment_flag := prior_treatment == TRUE]
  
  eligible_by_sample <- combined_meta[, .(
    sources = paste(unique(source), collapse = ";"),
    diagnosis_present = any(diagnosis_present, na.rm = TRUE),
    clinical_complete = any(clinical_complete == TRUE, na.rm = TRUE),
    prior_treatment = any(prior_treatment_flag == TRUE, na.rm = TRUE)
  ), by = sample_id]
  
  # Apply inclusion/exclusion criteria
  # Inclusion: proven diagnosis & complete clinical data
  # Exclusion: prior treatment OR insufficient data
  eligible_by_sample[, inclusion_status := ifelse(
    diagnosis_present & clinical_complete & !prior_treatment,
    "eligible", "ineligible"
  )]
  
  eligible_by_sample[, exclusion_reason := ifelse(
    inclusion_status == "eligible",
    "",
    paste(
      ifelse(!diagnosis_present, "missing_diagnosis", ""),
      ifelse(!clinical_complete, "incomplete_clinical_data", ""),
      ifelse(prior_treatment, "prior_treatment", ""),
      sep = ";"
    )
  )]
  
  # Clean up exclusion_reason formatting
  eligible_by_sample[, exclusion_reason := gsub("^;+|;+$", "", exclusion_reason)]
  eligible_by_sample[, exclusion_reason := gsub(";;+", ";", exclusion_reason)]
  
  # Final output: only eligible samples
  final_eligible <- eligible_by_sample[inclusion_status == "eligible",
                                      .(sample_id, sources, inclusion_status, exclusion_reason)]
  
  # Save final list
  fwrite(final_eligible, file.path(out_dir, "eligible_samples_final.csv"))
}