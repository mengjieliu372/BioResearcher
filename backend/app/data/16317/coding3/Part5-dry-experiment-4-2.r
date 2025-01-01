# Load necessary libraries
library(dplyr)   # For data manipulation
library(readr)   # For reading csv files
library(broom)   # For tidying model outputs
library(fs)      # For file system operations

# Specify file paths
alternative_lncRNA_expression_file <- "/path/to/output/combined_rna_seq_data.rds"  # Use the correct path
clinical_data_file <- "/path/to/output/clinical_attributes.csv"                     # Update this path accordingly

# Check if input files exist
if (!file.exists(alternative_lncRNA_expression_file)) {
  stop(paste("Error: The file", alternative_lncRNA_expression_file, "does not exist. Please check the file path."))
}

if (!file.exists(clinical_data_file)) {
  stop(paste("Error: The file", clinical_data_file, "does not exist. Please check the file path."))
}

# List files in the output directory for debugging
output_directory <- "/path/to/output/"  # Update this to your actual output directory
files_in_directory <- dir_ls(output_directory)
print("Files in the output directory:")
print(files_in_directory)

# Read the datasets
lncRNA_data <- readRDS(alternative_lncRNA_expression_file)  # Assuming this file is an RDS
clinical_data <- read_csv(clinical_data_file)

# Prepare the data for analysis
combined_data <- lncRNA_data %>%
  inner_join(clinical_data, by = "sample_id") %>%
  select(sample_id, lncRNA_expression = lncRNA_column, immunotherapy_response) # Adjust column names accordingly

combined_data$immunotherapy_response <- factor(combined_data$immunotherapy_response, levels = c("non-responder", "responder"))

# Fit the logistic regression model
model <- glm(immunotherapy_response ~ lncRNA_expression, data = combined_data, family = binomial)

# Summarize the results
results <- broom::tidy(model) %>%
  mutate(odds_ratio = exp(estimate),              # Calculate odds ratios
         conf_low = exp(estimate - 1.96 * std.error),  # 95% CI lower
         conf_high = exp(estimate + 1.96 * std.error))  # 95% CI upper

# Save the results
output_file <- "/path/to/output/lncRNA_predictive_model_results.csv"  # Specify the output file path
write_csv(results, output_file)

# Print a message indicating the completion
print("Logistic regression model fitted and results saved:")
print(results)