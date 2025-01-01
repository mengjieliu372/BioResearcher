# Load necessary library
library(dplyr)

# Set the directory path to the location where combined_samples.csv is found
directory_path <- "/path/to/local"  # Update this to your actual directory leading to 'local'

# Step 1: Check that the input file exists
input_file <- file.path(directory_path, "combined_samples.csv")  # Construct the full path

if (file.exists(input_file)) {
    # Read the input data from the combined samples metadata file
    samples_data <- read.csv(input_file)
    
    # Preview the data
    print(head(samples_data))

    # Step 2: Define the inclusion and exclusion criteria
    eligible_samples <- samples_data %>%
        filter(diagnosed == TRUE & clinical_complete == TRUE & prior_treatment == FALSE)

    # Step 3: Save the finalized list of eligible samples
    output_file <- "/path/to/output/final_eligible_samples.csv"  # Specify your output file path
    write.csv(eligible_samples, output_file, row.names = FALSE)

    # Step 4: Print a message indicating where the eligible samples were saved
    print(paste("Finalized list of eligible samples saved to:", output_file))
    print(head(eligible_samples))
} else {
    print("The input file does not exist, please check the file path.")
}