# filename: Part_1_dry_experiment_5.R
# This script identifies transcriptional cell states from normalized RNA-seq data using EcoTyper.
# Input: Normalized RNA-seq data (.txt or .csv file)
# Output: Cell state identification results (.txt or .csv file)

# Install remotes package if not already installed
if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes")
}

# Install EcoTyper from GitHub
remotes::install_github("ecoTyper/EcoTyper")

# Load necessary library
library(EcoTyper)

# Specify input and output file paths
input_file <- "data/normalized_data.csv"  # Change this to your actual input file path
output_file <- "results/cell_state_identification_results.csv"  # Change this to your desired output path

# Read the normalized RNA-seq data
normalized_data <- read.csv(input_file, row.names = 1)

# Identify transcriptional cell states using EcoTyper
cell_states_results <- EcoTyper(normalized_data)

# Save the results to a CSV file
write.csv(cell_states_results, output_file)

# Print a success message
print(paste("Cell state identification results saved to:", output_file))