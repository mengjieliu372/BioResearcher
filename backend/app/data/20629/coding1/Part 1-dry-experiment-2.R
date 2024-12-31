# filename: Part 1-dry-experiment-2.R
# This script scales RNA-seq data to TPM and converts non-standard formats to a uniform format.
# Input: RNA-seq data files in .txt or .csv format
# Output: RNA-seq data in TPM format, saved as a .txt or .csv file

# Load necessary libraries
library(dplyr)
library(readr)

# Function to convert counts to TPM
convert_to_tpm <- function(data) {
  gene_names <- data[[1]]
  counts <- as.matrix(data[-1])
  
  # Calculate TPM
  rpk <- counts / (1e-3 * rowSums(counts))
  tpm <- rpk / sum(rpk) * 1e6
  
  # Combine gene names with TPM values
  tpm_data <- data.frame(Gene = gene_names, tpm)
  return(tpm_data)
}

# Function to read, process and save RNA-seq data
process_rna_seq_data <- function(input_file, output_file) {
  # Check if the input file exists
  if (!file.exists(input_file)) {
    stop(paste("Error: The input file", input_file, "does not exist."))
  }
  
  # Read data
  if (grepl("\\.csv$", input_file)) {
    data <- read_csv(input_file)
  } else {
    data <- read_delim(input_file, delim = "\t")
  }
  
  # Convert data to TPM
  tpm_data <- convert_to_tpm(data)
  
  # Write output file
  if (grepl("\\.csv$", output_file)) {
    write_csv(tpm_data, output_file)
  } else {
    write_delim(tpm_data, output_file, delim = "\t")
  }
  
  print(paste("TPM data saved to:", output_file))
}

# Set your file paths here
input_file <- "input_file.csv"  # Change this to your input file path
output_file <- "output_file.csv" # Change this to your desired output file path

# Execute processing
process_rna_seq_data(input_file, output_file)