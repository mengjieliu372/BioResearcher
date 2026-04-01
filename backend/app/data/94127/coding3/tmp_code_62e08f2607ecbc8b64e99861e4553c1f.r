exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 1-dry-experiment-1: Sample search (proxy using allowed local files)
# Constraints: use only allowed inputs, handle missing files gracefully, write outputs under /workspace/coding3

suppressPackageStartupMessages({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    install.packages("data.table")
  }
  library(data.table)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
}

# Allowed input files
f_meta  <- "/workspace/data/GSE267611_sample_meta_out.txt.gz"
f_raw   <- "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz"
f_cyto  <- "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"

# Helper: standardize to shared schema
standardize_samples <- function(dt, source_label) {
  if (is.null(dt) || nrow(dt) == 0) {
    return(data.table(
      sample_id = NA_character_,
      source = source_label,
      tissue_type = NA_character_,
      collection_date = NA_character_,
      characteristics = NA_character_
    ))
  }
  cn <- names(dt)

  # sample_id: find column containing "sample"
  sample_col <- cn[grepl("sample", cn, ignore.case = TRUE)]
  if (length(sample_col) == 0) sample_col <- cn[1]
  sample_id <- as.character(dt[[sample_col[1]]])

  # tissue_type: column containing tissue/histology
  tissue_col <- cn[grepl("tissue|histolog|type", cn, ignore.case = TRUE)]
  tissue_type <- if (length(tissue_col) > 0) as.character(dt[[tissue_col[1]]]) else NA_character_

  # collection_date: column containing date
  date_col <- cn[grepl("date", cn, ignore.case = TRUE)]
  collection_date <- if (length(date_col) > 0) as.character(dt[[date_col[1]]]) else NA_character_

  # characteristics: concatenate key=value for remaining columns
  char_cols <- setdiff(cn, unique(c(sample_col[1], tissue_col[1], date_col[1])))
  characteristics <- if (length(char_cols) > 0) {
    apply(dt[, ..char_cols], 1, function(x) {
      paste(paste(char_cols, x, sep="="), collapse="; ")
    })
  } else {
    NA_character_
  }

  data.table(
    sample_id = sample_id,
    source = source_label,
    tissue_type = tissue_type,
    collection_date = collection_date,
    characteristics = characteristics
  )
}

# Read file safely
safe_read <- function(path, ...) {
  if (!file.exists(path)) {
    warning(sprintf("Missing file: %s. Creating placeholder.", path))
    return(NULL)
  }
  tryCatch({
    data.table::fread(path, ...)
  }, error = function(e) {
    warning(sprintf("Failed to read %s: %s. Creating placeholder.", path, e$message))
    return(NULL)
  })
}

# 1) GSE267611 sample metadata
dt_meta <- safe_read(f_meta)
samples_meta <- standardize_samples(dt_meta, "GSE267611_sample_meta")

# 2) GSE91061 raw counts -> sample IDs are column names (excluding gene column)
dt_raw <- safe_read(f_raw)
samples_raw <- NULL
if (!is.null(dt_raw) && ncol(dt_raw) > 1) {
  sample_ids <- setdiff(names(dt_raw), names(dt_raw)[1])
  samples_raw <- data.table(
    sample_id = sample_ids,
    source = "GSE91061_raw_counts",
    tissue_type = NA_character_,
    collection_date = NA_character_,
    characteristics = NA_character_
  )
} else {
  samples_raw <- standardize_samples(NULL, "GSE91061_raw_counts")
}

# 3) GSE91061 cytolytic score file
dt_cyto <- safe_read(f_cyto)
samples_cyto <- standardize_samples(dt_cyto, "GSE91061_cytolytic_score")

# Combine using shared schema
combined <- rbindlist(list(samples_meta, samples_raw, samples_cyto), fill = TRUE)

# Add note for task context
combined[, note := "Proxy sample list derived from allowed local/GEO files; TCGA/GTEx/biobank access not available in this environment."]

# Save output
out_file <- file.path(out_dir, "sample_list_final.csv")
fwrite(combined, out_file)

# Optional: print summary
cat(sprintf("Wrote %d records to %s\n", nrow(combined), out_file))