# filename: Part_4_dry_experiment_2.R
# This script filters out low-count genes from a normalized RNA-seq dataset 
# by removing genes with less than 10 counts across all samples.

# Load necessary packages
library(dplyr)

# Set input and output file paths
input_file <- "data/normalized_data.csv" # Input: Path to the normalized RNA-seq data
output_file <- "data/filtered_normalized_data.csv" # Output: Path to save the filtered data

# Read in normalized RNA-seq data
normalized_data <- read.csv(input_file, row.names = 1)

# Filter out low-count genes (less than 10 counts across all samples)
filtered_data <- normalized_data[rowSums(normalized_data) >= 10, ]

# Save the filtered data to a new CSV file
write.csv(filtered_data, file = output_file)

# Print message indicating completion
print("Filtering complete: Low-count genes removed and data saved.")