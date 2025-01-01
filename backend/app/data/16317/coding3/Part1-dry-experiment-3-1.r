# Load necessary libraries
library(dplyr)  # For data manipulation

# Define a file path for the local GTEx dataset
gtex_file_path <- "/path/to/local/gtex_data.csv"  # Specify your local path
output_directory <- dirname(gtex_file_path)

# Step 1: Create directory if it doesn't exist
if (!dir.exists(output_directory)) {
  dir.create(output_directory, recursive = TRUE)
}

# Step 2: Download the dataset if it doesn't exist
# Note: Please replace 'example_data_url' with the actual GTEx dataset URL.
example_data_url <- "https://example.com/path/to/sample_gtex_data.csv"

if (!file.exists(gtex_file_path)) {
  download.file(example_data_url, gtex_file_path)
}

# Step 3: Check if the file exists before proceeding
if (!file.exists(gtex_file_path)) {
  stop("The GTEx data file does not exist. Please check the file path or download the data.")
}

# Step 4: Read in the GTEx data
gtex_df <- read.csv(gtex_file_path, stringsAsFactors = FALSE)

# Step 5: Filter for 'sarcoma' tissue type
sarcoma_samples <- gtex_df %>% 
  filter(tissue_type == "sarcoma")  # Assuming 'tissue_type' is the correct column name

# Step 6: Select relevant columns (adjust based on actual column names)
filtered_sarcoma_samples <- sarcoma_samples %>% 
  select(sample_id, sample_type, collection_date, patient_demographics)  # Adjust to actual column names

# Step 7: Save the filtered results to a CSV file
output_file_path <- "/path/to/output/sarcoma_samples_filtered.csv"  # Define your output path
output_directory <- dirname(output_file_path)

# Create output directory if it doesn't exist
if (!dir.exists(output_directory)) {
  dir.create(output_directory, recursive = TRUE)
}

write.csv(filtered_sarcoma_samples, output_file_path, row.names = FALSE)

# Print confirmation message
print(paste("Filtered sarcoma samples saved to:", output_file_path))