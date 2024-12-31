# filename: Part_4_dry_experiment_1.R
# This script normalizes RNA-seq data using DESeq2's median of ratios method, ensuring comparability across samples.

# Load necessary libraries
if (!requireNamespace("DESeq2", quietly = TRUE)) {
    install.packages("BiocManager")
    BiocManager::install("DESeq2")
}

library(DESeq2)

# Specify the directory where the raw count data CSV files are located
data_directory <- "data"

# List and load the raw count data CSV files
count_files <- list.files(data_directory, pattern = "*.csv", full.names = TRUE)

# Read count data from all files and combine them into one data frame
count_data_list <- lapply(count_files, function(file) {
    read.csv(file, row.names = 1)
})
combined_counts <- do.call(cbind, count_data_list)

# Create DESeq2 dataset object
dds <- DESeqDataSetFromMatrix(countData = combined_counts,
                              colData = data.frame(row.names = colnames(combined_counts)),
                              design = ~ 1)

# Run DESeq normalization
dds <- DESeq(dds)
normalized_counts <- counts(dds, normalized = TRUE)

# Save normalized counts to a CSV file
write.csv(normalized_counts, file = file.path(data_directory, "normalized_counts.csv"))

print("Normalized RNA-seq data has been saved to 'normalized_counts.csv'.")