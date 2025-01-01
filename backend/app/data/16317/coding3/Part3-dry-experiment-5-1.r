# Load the combined RNA sequencing data
rna_seq_data <- readRDS("/path/to/output/combined_rna_seq_data.rds")  # Adjust the path

# Print the structure of the data
str(rna_seq_data)

# Optionally, display the first few rows of the data
head(rna_seq_data)