# Load necessary library
library(dplyr)

# Step 1: Creating a data frame to document challenges and resolutions
challenges_df <- data.frame(
  Date = Sys.Date(),  # Current date
  Task_ID = "Part 5-dry-experiment-5",
  Challenge = c(
    "Data quality of RNA sequencing files was inconsistent leading to missing values.",
    "Difficulty in normalizing expression data across different datasets due to compatibility issues.",
    "Inconsistent sample identifiers across different sources created challenges in merging datasets."
  ),
  Suggested_Solution = c(
    "Implement data imputation methods and quality control checks to handle missing values.",
    "Utilize robust normalization methods like quantile normalization that can handle variances.",
    "Standardize sample identification codes across datasets before merging."
  ),
  stringsAsFactors = FALSE
)

# Step 2: Define the file path to save the report
output_file_path <- "/path/to/output/challenges_report.csv"

# Step 3: Write the challenges data frame to a CSV file
write.csv(challenges_df, output_file_path, row.names = FALSE)

# Step 4: Print confirmation message
print(paste("Challenges documented and saved to:", output_file_path))