# Load necessary libraries
library(limma)  # Ensure the limma package is loaded

# Load the combined RNA sequencing data (from previous output)
combined_rna_seq_data <- readRDS("/path/to/output/combined_rna_seq_data.rds")

# Load the design matrix (from previous output)
design_matrix <- readRDS("/path/to/output/design_matrix.rds")

# Fit a linear model using lmFit
fitted_model <- lmFit(combined_rna_seq_data, design_matrix)

# Save the fitted model for later use
saveRDS(fitted_model, "/path/to/output/fitted_linear_model.rds")  # Specify the correct path to save

print("Fitted linear model has been saved successfully.")