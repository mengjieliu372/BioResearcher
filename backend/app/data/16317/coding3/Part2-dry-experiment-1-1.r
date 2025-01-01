# Load the necessary library for accessing GEO datasets
if (!requireNamespace("GEOquery", quietly = TRUE)) {
  install.packages("BiocManager")
  BiocManager::install("GEOquery")
}

library(GEOquery)

# Define the list of dataset identifiers
dataset_ids <- c("GSE202361", "GSE205492", "GSE161616", "GSE57750", 
                 "GSE68591", "GSE55466", "GSE55465", "GSE267611", 
                 "GSE230773", "GSE191132", "GSE213065", "GSE247026", 
                 "GSE243904", "GSE243759")

# Define the output directory for the downloaded files
output_dir <- "/path/to/downloaded_data/rna_seq"

# Create the output directory if it doesn't exist
if(!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Function to download GEO datasets with retry
download_geodata <- function(id, retries = 3) {
  for (attempt in 1:retries) {
    tryCatch({
      gse <- getGEO(id, GSEMatrix = TRUE, getGPL = FALSE)
      if (length(gse) > 0) {
        expr_set <- gse[[1]]
        output_file <- file.path(output_dir, paste0(id, "_expression.txt"))
        write.table(exprs(expr_set), file = output_file, sep = "\t", quote = FALSE, col.names = NA)
        print(paste("Downloaded and saved data for:", id))
        return(TRUE)  # Exit successfully
      } else {
        print(paste("No data found for:", id))
        return(FALSE)  # No data handling
      }
    }, error = function(e) {
      if (attempt == retries) {
        print(paste("Failed to download", id, "after", retries, "attempts:", e$message))
      } else {
        Sys.sleep(5)  # Delay before retrying
        print(paste("Retrying to download", id, "Attempt:", attempt + 1))
      }
    })
  }
  return(FALSE)  # If all attempts fail
}

# Loop through dataset IDs and download each
for (id in dataset_ids) {
  download_geodata(id)
}

# Print final confirmation message
print("Attempted to download all specified RNA sequencing datasets.")