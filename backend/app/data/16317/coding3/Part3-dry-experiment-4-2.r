# Load required libraries
library(limma)  # Make sure the limma package is loaded

# Define the directory where the output files are saved
output_directory <- "/path/to/output"  # Update this with the actual path

# List all .rds files in the output directory to help identify the fitted model
available_models <- list.files(output_directory, pattern = "\\.rds$", full.names = TRUE)

# Print the available files to identify the fitted linear model
print("Available .rds files:")
print(available_models)

# Define the correct path to the fitted linear model object (manual adjustment after checking available models)
fitted_model_path <- "/path/to/output/actual_fitted_linear_model.rds"  # Update after checking available files

# Check if the fitted linear model file exists
if (!file.exists(fitted_model_path)) {
  stop(paste("Error: The fitted linear model file does not exist at the specified path:", fitted_model_path))
}

# Load the fitted linear model object
fitted_model <- readRDS(fitted_model_path)

# Apply the eBayes function to compute empirical Bayes statistics
ebayes_result <- eBayes(fitted_model)

# Save the eBayes result to an RDS file for future use
saveRDS(ebayes_result, "/path/to/output/empirical_bayes_statistics.rds")  # Replace with your desired save path

# Print the result structure for verification
print(ebayes_result)