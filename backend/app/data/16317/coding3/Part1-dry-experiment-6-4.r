# Load necessary libraries
library(dplyr)
library(readr)

# Update the input and output paths based on your findings
input_file <- "/data/output/combined_samples.csv"  # The corrected input file path
output_file <- "/data/output/liposarcoma_detailed_characteristics.csv"  # The output file path

# Check if the input file exists before proceeding
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
  # If the file does not exist, print an error message
  stop(paste("Error: The file", input_file, "does not exist. Please check the file path."))
}