# Set file paths for the RNA sequencing data
tcga_file_path <- "/path/to/downloaded_data/rna_seq/GSE202361_expression.txt" # Adjust as needed for actual file
gse_file_path <- "/path/to/downloaded_data/rna_seq/GSE202361_expression.txt" # Adjust as needed

# Ensure that the files exist to avoid errors during the preview
if (!file.exists(tcga_file_path) || !file.exists(gse_file_path)) {
  stop("One or more files do not exist.")
}

# Read initial lines of the TCGA file to verify structure
tcga_preview <- readLines(tcga_file_path, n = 10) # Read the first 10 lines
cat("Preview of TCGA file:\n")
cat(tcga_preview, sep = "\n") # Display the lines

# Read initial lines of the GSE file to verify structure
gse_preview <- readLines(gse_file_path, n = 10) # Read the first 10 lines
cat("\nPreview of GSE file:\n")
cat(gse_preview, sep = "\n") # Display the lines