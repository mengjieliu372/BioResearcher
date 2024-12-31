# filename: Part_1_dry_experiment_7.R
# This script tries to install the ESTIMATE package from Bioconductor, and then analyzes
# the tumor microenvironment to calculate stromal and immune scores based on the provided expression data.

# Install BiocManager if it's not already installed
if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager")
}

# Use a workaround to install ESTIMATE since it's not available in the Bioconductor version
tryCatch({
  # Check if any existing installation of 'estimate' exists; if not, fetch from GitHub directly
  if (!requireNamespace("estimate", quietly = TRUE)) {
    remotes::install_github("molgenis/ESTIMATE") # Fetch from GitHub for alternatives
  }
}, error = function(e) {
  stop("Unable to install the ESTIMATE package. Please check internet connection or package availability.")
})

# Load the required library
library(estimate)

# Read in expression data
input_file <- 'data/expression_data.txt' # change input file name as necessary
expression_data <- read.table(input_file, header = TRUE, row.names = 1)

# Ensure the data is in the correct format for ESTIMATE
expression_matrix <- as.matrix(expression_data)

# Run the ESTIMATE algorithm to get scores
estimate_scores <- estimateScore(expression_matrix)

# Extract stromal and immune scores
stromal_score <- estimate_scores$stromal_score
immune_score <- estimate_scores$immune_score

# Create a data frame for scores
scores_df <- data.frame(Sample=colnames(expression_matrix),
                        StromalScore=stromal_score,
                        ImmuneScore=immune_score)

# Save scores to a CSV file
output_file <- 'data/estimate_scores.csv' # change output file name as necessary
write.csv(scores_df, output_file, row.names = FALSE)

# Print the scores data frame for inspection
print(scores_df)