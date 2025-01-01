# Load necessary libraries
library(DESeq2)        # For DESeq normalization
library(gcrma)         # For gcrma normalization
library(data.table)    # For reading and writing data efficiently

# Set input file paths (update these paths to the correct locations)
file_paths <- list(
  "/path/to/downloaded_data/rna_seq/GSE202361_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE205492_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE161616_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE57750_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE68591_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE55466-GPL10558_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE55466-GPL14951_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE55465_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE267611_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE230773-GPL18573_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE230773-GPL22790_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE191132_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE213065-GPL20301_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE213065-GPL24676_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE247026_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE243904_expression.txt",
  "/path/to/downloaded_data/rna_seq/GSE243759_expression.txt"
)

# Initialize an empty list to store all datasets
all_data <- list()

# Check for file existence and read the RNA-seq data
for (file_path in file_paths) {
  if (file.exists(file_path)) {
    expression_data <- fread(file_path) # Read the expression data
    all_data[[file_path]] <- expression_data
  } else {
    stop(paste("File does not exist or is not readable:", file_path))
  }
}

# Combine all datasets (assuming they have the same gene IDs)
combined_data <- Reduce(function(x, y) merge(x, y, by="gene_id", all=TRUE), all_data)

# Proceed with further steps...
