# Load necessary library
library(dplyr)

# Step 1: Check files in the specified directory
directory_path <- "/path/to/directory"  # Update this to the correct directory
files <- list.files(directory_path)

# Print the available files to verify the presence of combined_samples.csv
print(files)

# Step 2: If combined_samples.csv is present, read the input data
input_file <- file.path(directory_path, "combined_samples.csv")  # Construct the full path
if (file.exists(input_file)) {
    samples_data <- read.csv(input_file)
    print(head(samples_data))

    # Step 3: Define the inclusion and exclusion criteria
    eligible_samples <- samples_data %>%
        filter(diagnosed == TRUE & clinical_complete == TRUE & prior_treatment == FALSE)

    # Step 4: Saving the finalized list of eligible samples
    output_file <- "/path/to/output/final_eligible_samples.csv"  # Specify your output file path
    write.csv(eligible_samples, output_file, row.names = FALSE)

    # Print a message indicating where the eligible samples were saved
    print(paste("Finalized list of eligible samples saved to:", output_file))
    print(head(eligible_samples))
} else {
    print("The input file does not exist, please check the file path.")
}