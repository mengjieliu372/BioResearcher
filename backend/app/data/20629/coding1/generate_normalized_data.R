# filename: generate_normalized_data.R
# This script generates a sample normalized RNA-seq dataset for demonstration purposes.

# Set the output file path for the sample normalized data
output_file <- "data/normalized_data.csv"

# Set a random seed for reproducibility
set.seed(42)

# Generate a sample normalized data frame with 100 genes and 10 samples
num_genes <- 100
num_samples <- 10
sample_data <- matrix(rpois(num_genes * num_samples, lambda = 20), nrow = num_genes, ncol = num_samples)

# Set row names (genes) and column names (samples)
rownames(sample_data) <- paste0("Gene", 1:num_genes)
colnames(sample_data) <- paste0("Sample", 1:num_samples)

# Convert to a data frame
normalized_data <- as.data.frame(sample_data)

# Save the sample normalized data frame as a CSV file
write.csv(normalized_data, file = output_file)

# Print message indicating completion
print("Sample normalized data generated and saved as 'normalized_data.csv'.")