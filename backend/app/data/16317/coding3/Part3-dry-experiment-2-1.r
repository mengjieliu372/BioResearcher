# Load necessary packages
library(limma)  # For creating the design matrix

# Step 2: Load the RNA sequencing data
# Assuming the combined RNA seq data is saved as a .rds file
rna_seq_data <- readRDS("/path/to/output/combined_rna_seq_data.rds")  # Change the path as necessary

# Step 3: Define experimental conditions
# Here, we assume you have a predetermined vector indicating the group assignments (e.g., treatment vs. control)
# Example vector: c("Control", "Control", "Treatment", "Treatment", ...) for each sample
experimental_conditions <- c(rep("Control", 2), rep("Treatment", 2))  # Adjust as necessary

# Step 4: Create the Design Matrix
# Using the experimental conditions to create a design matrix
design_matrix <- model.matrix(~ experimental_conditions)

# Step 5: Save the Design Matrix
saveRDS(design_matrix, "/path/to/output/design_matrix.rds")  # Save the design matrix to a file

# Print for confirmation
print("Design matrix created and saved successfully.")
print(design_matrix)