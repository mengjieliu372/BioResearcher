exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 2-dry-experiment-1: "Download" RNA-seq data (offline staging from allowlisted local files)
# Constraints: use only allowlisted input files; no directory scanning; graceful handling.

suppressPackageStartupMessages({
  library(data.table)
})

# Output directory
out_dir <- "/workspace/coding3/part2_downloads"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# Dataset IDs requested
dataset_ids <- c(
  "GSE202361", "GSE205492", "GSE161616", "GSE57750", "GSE68591",
  "GSE55466", "GSE55465", "GSE267611", "GSE230773", "GSE191132",
  "GSE213065", "GSE247026", "GSE243904", "GSE243759"
)

# Map dataset IDs to allowlisted input files (only those explicitly permitted)
input_map <- list(
  GSE202361 = c("/workspace/data/GSE202361_AllSamples_TPM.txt.gz",
                "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz"),
  GSE247026 = c("/workspace/data/GSE247026_Sample_genes_fpkm.xlsx"),
  GSE213065 = c("/workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz"),
  GSE230773 = c("/workspace/data/GSE230773_Read_counts.xlsx"),
  GSE243904 = c("/workspace/data/GSE243904_DGE_NORM_IB11_PRMT5_Treated_vs_notreated_LIMMA_T-TEST_AFFYX.txt.gz")
  # NOTE: Other requested datasets are not present in the allowlist for this task.
)

# Create a manifest table
manifest <- data.table(
  dataset_id = character(),
  source_file = character(),
  dest_file = character(),
  status = character(),
  note = character()
)

# Process each dataset
for (id in dataset_ids) {
  srcs <- input_map[[id]]
  if (is.null(srcs) || length(srcs) == 0) {
    # Create a placeholder file for missing datasets
    placeholder <- file.path(out_dir, paste0(id, "_MISSING.txt"))
    writeLines(
      sprintf("No allowlisted input file available for %s in this task.", id),
      con = placeholder
    )
    manifest <- rbind(
      manifest,
      data.table(
        dataset_id = id,
        source_file = NA_character_,
        dest_file = placeholder,
        status = "missing",
        note = "Created placeholder due to unavailable allowlisted input."
      )
    )
  } else {
    for (src in srcs) {
      if (file.exists(src)) {
        dest <- file.path(out_dir, basename(src))
        ok <- FALSE
        try({
          ok <- file.copy(src, dest, overwrite = TRUE)
        }, silent = TRUE)
        manifest <- rbind(
          manifest,
          data.table(
            dataset_id = id,
            source_file = src,
            dest_file = dest,
            status = ifelse(ok, "copied", "copy_failed"),
            note = ifelse(ok, "Staged from local allowlisted file.",
                          "Copy failed; placeholder not created.")
          )
        )
      } else {
        # If allowlisted path is missing (should not happen), create placeholder
        placeholder <- file.path(out_dir, paste0(id, "_MISSING.txt"))
        writeLines(
          sprintf("Allowlisted file not found for %s: %s", id, src),
          con = placeholder
        )
        manifest <- rbind(
          manifest,
          data.table(
            dataset_id = id,
            source_file = src,
            dest_file = placeholder,
            status = "missing",
            note = "Allowlisted path missing; created placeholder."
          )
        )
      }
    }
  }
}

# Save manifest
manifest_path <- "/workspace/coding3/part2_download_manifest.csv"
fwrite(manifest, manifest_path)

# Also write a brief log
log_path <- "/workspace/coding3/part2_download_log.txt"
writeLines(c(
  "Part 2-dry-experiment-1: RNA-seq data staging (offline).",
  sprintf("Output directory: %s", out_dir),
  sprintf("Manifest: %s", manifest_path),
  "Note: Sample selection criteria from Part 1 not applied due to input constraints."
), con = log_path)