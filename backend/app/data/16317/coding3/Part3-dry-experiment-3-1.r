# Load required libraries
library(limma)  # For linear model fitting

# Define file paths
rna_seq_data_file <- "/path/to/output/combined_rna_seq_data.rds"  # Ensure this path is correct
design_matrix_file <- "/path/to/output/design_matrix.rds"         # Ensure this path is correct
fitted_model_output_file <- "/path/to/output/fitted_linear_model.rds"  # Update the output path as needed

# Load RNA sequencing data
rna_seq_data <- readRDS(rna_seq_data_file)  # Read in the combined RNA seq data
# Load the design matrix
design_matrix <- readRDS(design_matrix_file)  # Read in the design matrix

# Fit the linear model to the data
fitted_model <- lmFit(rna_seq_data, design_matrix)

# Save the fitted model object
saveRDS(fitted_model, fitted_model_output_file)

# Print a message to indicate successful fit
print("Linear model has been successfully fitted and saved.")