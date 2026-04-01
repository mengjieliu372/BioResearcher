exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 1-dry-experiment-3: Filter GTEx data by 'sarcoma' tissue type
# Constraints: use only allowlisted input files; graceful handling; save under /workspace/coding3

suppressPackageStartupMessages({
  library(data.table)
})

output_dir <- "/workspace/coding3"
if (!dir.exists(output_dir)) dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# Allowlisted inputs
files <- list(
  meta = "/workspace/data/GSE267611_sample_meta_out.txt.gz",
  gse91061_raw = "/workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.raw.csv.gz",
  gse91061_cyt = "/workspace/data/GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt.gz"
)

# Helper to map to shared schema
map_to_schema <- function(dt, source_name) {
  # Standard schema
  schema_cols <- c("sample_id", "tissue_type", "collection_date", "age", "sex", "source", "notes")
  if (is.null(dt) || nrow(dt) == 0) {
    return(data.table(sample_id = character(),
                      tissue_type = character(),
                      collection_date = character(),
                      age = character(),
                      sex = character(),
                      source = character(),
                      notes = character()))
  }

  # Try to infer columns
  cn <- tolower(names(dt))
  get_col <- function(patterns) {
    idx <- which(sapply(patterns, function(p) grepl(p, cn)))
    if (length(idx) > 0) names(dt)[idx[1]] else NA_character_
  }

  sample_col <- get_col(c("geo_accession", "sample", "sample_id", "gsm", "id"))
  tissue_col <- get_col(c("tissue", "histology", "diagnosis", "disease", "tumor", "sarcoma"))
  date_col   <- get_col(c("collection", "date", "time"))
  age_col    <- get_col(c("age"))
  sex_col    <- get_col(c("sex", "gender"))

  out <- data.table(
    sample_id = if (!is.na(sample_col)) as.character(dt[[sample_col]]) else NA_character_,
    tissue_type = if (!is.na(tissue_col)) as.character(dt[[tissue_col]]) else NA_character_,
    collection_date = if (!is.na(date_col)) as.character(dt[[date_col]]) else NA_character_,
    age = if (!is.na(age_col)) as.character(dt[[age_col]]) else NA_character_,
    sex = if (!is.na(sex_col)) as.character(dt[[sex_col]]) else NA_character_,
    source = source_name,
    notes = NA_character_
  )

  # Ensure schema columns
  for (col in schema_cols) {
    if (!col %in% names(out)) out[, (col) := NA_character_]
  }
  out[, ..schema_cols]
}

# Read metadata file (primary source)
meta_dt <- NULL
if (file.exists(files$meta)) {
  meta_dt <- tryCatch({
    fread(files$meta)
  }, error = function(e) {
    warning("Failed to read metadata file: ", files$meta, " | ", conditionMessage(e))
    NULL
  })
} else {
  warning("Missing file: ", files$meta)
}

# Filter for sarcoma based on any tissue/diagnosis columns
meta_filtered <- NULL
if (!is.null(meta_dt) && nrow(meta_dt) > 0) {
  cn <- tolower(names(meta_dt))
  candidate_cols <- names(meta_dt)[grepl("tissue|histology|diagnosis|disease|tumor", cn)]
  if (length(candidate_cols) == 0) {
    # fallback to all columns
    candidate_cols <- names(meta_dt)
  }
  # Create logical vector if any column contains 'sarcoma'
  sarcoma_hits <- apply(meta_dt[, ..candidate_cols], 1, function(row) {
    any(grepl("sarcoma", tolower(paste(row, collapse = " "))))
  })
  meta_filtered <- meta_dt[sarcoma_hits]
} else {
  meta_filtered <- data.table()
}

meta_mapped <- map_to_schema(meta_filtered, "GSE267611_sample_meta_out")

# Read GSE91061 raw counts to extract sample IDs (no tissue info expected)
raw_mapped <- NULL
if (file.exists(files$gse91061_raw)) {
  raw_mapped <- tryCatch({
    # read only header/first row to get column names
    raw_dt <- fread(files$gse91061_raw, nrows = 1)
    # gene ID likely first column; sample IDs are other columns
    if (ncol(raw_dt) > 1) {
      sample_ids <- setdiff(names(raw_dt), names(raw_dt)[1])
      # filter if any sample id contains sarcoma
      sample_ids <- sample_ids[grepl("sarcoma", tolower(sample_ids))]
      if (length(sample_ids) > 0) {
        data.table(
          sample_id = sample_ids,
          tissue_type = "sarcoma",
          collection_date = NA_character_,
          age = NA_character_,
          sex = NA_character_,
          source = "GSE91061_raw_counts",
          notes = "Sample IDs matched 'sarcoma' keyword"
        )
      } else {
        data.table()
      }
    } else {
      data.table()
    }
  }, error = function(e) {
    warning("Failed to parse raw counts header: ", files$gse91061_raw, " | ", conditionMessage(e))
    data.table()
  })
} else {
  warning("Missing file: ", files$gse91061_raw)
  raw_mapped <- data.table()
}

# Read cytolytic score table (if metadata-like)
cyt_mapped <- NULL
if (file.exists(files$gse91061_cyt)) {
  cyt_mapped <- tryCatch({
    cyt_dt <- fread(files$gse91061_cyt)
    # attempt to filter if any row contains sarcoma
    if (nrow(cyt_dt) > 0) {
      sarcoma_hits <- apply(cyt_dt, 1, function(row) {
        any(grepl("sarcoma", tolower(paste(row, collapse = " "))))
      })
      cyt_filtered <- cyt_dt[sarcoma_hits]
      map_to_schema(cyt_filtered, "GSE91061_cytolytic_score")
    } else {
      data.table()
    }
  }, error = function(e) {
    warning("Failed to read cytolytic score file: ", files$gse91061_cyt, " | ", conditionMessage(e))
    data.table()
  })
} else {
  warning("Missing file: ", files$gse91061_cyt)
  cyt_mapped <- data.table()
}

# Combine using shared schema
all_combined <- rbindlist(list(meta_mapped, raw_mapped, cyt_mapped), fill = TRUE)

# If no data, create placeholder empty table with schema
if (nrow(all_combined) == 0) {
  warning("No sarcoma-related samples found in allowlisted inputs; writing placeholder output.")
  all_combined <- data.table(
    sample_id = character(),
    tissue_type = character(),
    collection_date = character(),
    age = character(),
    sex = character(),
    source = character(),
    notes = character()
  )
}

# Save output
out_file <- file.path(output_dir, "gtex_sarcoma_sample_metadata.csv")
fwrite(all_combined, out_file)

message("Saved output to: ", out_file)