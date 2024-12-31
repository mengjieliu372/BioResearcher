# filename: Part_4_dry_experiment_1_v4.R
# This script normalizes RNA-seq data using DESeq2's median of ratios method, ensuring comparability across samples.
# It checks for empty input files before processing, with improved error handling.

# Load necessary libraries
if (!requireNamespace("DESeq2", quietly = TRUE)) {
    install.packages("BiocManager")
    BiocManager::install("DESeq2")
}

library(DESeq2)

# Specify the directory where the raw count data CSV files are located
data_directory <- "data"

# List CSV files in the data directory
count_files <- list.files(data_directory, pattern = "*.csv", full.names = TRUE)

# Initialize a list to store valid count data
valid_count_data_list <- list()

# Check each file for content before reading
for (file in count_files) {
    if (file.info(file)$size > 0) {  # Check if the file is not empty
        count_data <- tryCatch({
            read.csv(file, row.names = 1)
        }, error = function(e) {
            message(paste("Error reading file:", file, "-", e$message))
            return(NULL)
        })
        
        if (!is.null(count_data) && nrow(count_data) > 0) {
            valid_count_data_list[[file]] <- count_data
        } else {
            warning(paste("File", file, "has no valid data and will be skipped."))
        }
    } else {
        warning(paste("File", file, "is empty and will be skipped."))
    }
}

# Combine valid count data into one data frame
if (length(valid_count_data_list) == 0) {
    stop("No valid count data found. Please check your input files.")
}

combined_counts <- do.call(cbind, valid_count_data_list)

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