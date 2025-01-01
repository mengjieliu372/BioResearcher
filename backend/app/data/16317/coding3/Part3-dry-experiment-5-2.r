# Assuming the first column is the gene identifiers, convert the rest to numeric
# Extract numeric data while excluding non-numeric columns
expression_matrix <- as.matrix(rna_seq_data[ , -1])  # This assumes the first column is non-numeric

# Ensure all data in the matrix is numeric
if (!all(sapply(expression_matrix, is.numeric))) {
    stop("The expression matrix contains non-numeric data.")
}

# Now fit the linear model using the numeric matrix and the design matrix
fit <- lmFit(expression_matrix, design)

# Save the fitted model
saveRDS(fit, "/path/to/output/fitted_linear_model.rds")

# Print a confirmation message
print("Fitted linear model saved successfully.")