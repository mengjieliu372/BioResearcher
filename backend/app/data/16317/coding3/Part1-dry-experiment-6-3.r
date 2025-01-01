# Load necessary libraries
library(dplyr)
library(readr)

# Update the input and output paths based on your findings
input_file <- "/workspace/path/to/your/combined_samples.csv"  # Correct this to what you find
output_file <- "/workspace/path/to/output/liposarcoma_detailed_characteristics.csv"  # Your desired output path

# Proceed with the same logic as before after confirming the file exists
if (file.exists(input_file)) {
  
  # Step 2: Read the final list of eligible samples
  eligible_samples <- read_csv(input_file)
  
  # Step 3: Process the data to select relevant characteristics
  detailed_characteristics <- eligible_samples %>%
    select(Sample_ID, Patient_Age, Gender, Tumor_Grade, Tumor_Stage)  # Adjust based on actual columns in your dataset
  
  # Step 4: Save the processed dataset to a CSV file
  write_csv(detailed_characteristics, output_file)

  # Print a message indicating successful execution
  print("Structured dataset containing detailed characteristics of each selected sample has been saved.")
  
} else {
  stop(paste("Error: The file", input_file, "does not exist. Please check the file path."))
}