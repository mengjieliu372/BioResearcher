# filename: Part_1_dry_experiment_5_alternative.R
# This script identifies transcriptional cell states from normalized RNA-seq data using Seurat.
# Input: Normalized RNA-seq data (.txt or .csv file)
# Output: Cell state identification results (.txt or .csv file)

# Install Seurat if not already installed
if (!requireNamespace("Seurat", quietly = TRUE)) {
  install.packages("Seurat")
}

# Load necessary library
library(Seurat)

# Specify input and output file paths
input_file <- "data/normalized_data.csv"  # Change this to your actual input file path
output_file <- "results/cell_state_identification_results.csv"  # Change this to your desired output path

# Check if the input file exists
if (!file.exists(input_file)) {
  stop(paste("Input file does not exist:", input_file))
}

# Read the normalized RNA-seq data
normalized_data <- read.csv(input_file, row.names = 1)

# Create a Seurat object
seurat_obj <- CreateSeuratObject(counts = normalized_data)

# Normalize the data (if not already normalized)
seurat_obj <- NormalizeData(seurat_obj)

# Find variable features
seurat_obj <- FindVariableFeatures(seurat_obj)

# Scale the data
seurat_obj <- ScaleData(seurat_obj)

# Perform dimensionality reduction
seurat_obj <- RunPCA(seurat_obj)

# Clustering cells
seurat_obj <- FindNeighbors(seurat_obj, dims = 1:10)
seurat_obj <- FindClusters(seurat_obj)

# Get cell state identification results
cell_states_results <- seurat_obj@meta.data

# Save the results to a CSV file
write.csv(cell_states_results, output_file)

# Print a success message
print(paste("Cell state identification results saved to:", output_file))