   # Load necessary library
   if (!require("dplyr")) {
       install.packages("dplyr")  # Install if not already available
   }
   library(dplyr)   # For data manipulation

   # Define the path to local biobank data (update this to your actual file path)
   biobank_data_path <- "/home/username/data/biobank_data.csv"  # Replace with your actual path

   # Check if the file exists before reading
   if (!file.exists(biobank_data_path)) {
       stop(paste("File not found:", biobank_data_path))  # Halt execution and provide a message if file does not exist
   }

   # Load local biobank data using base R
   local_biobank_data <- read.csv(biobank_data_path)

   # Filter for unique liposarcoma cases 
   liposarcoma_data <- local_biobank_data %>%
       filter(Diagnosis == "Liposarcoma") %>%  # Assuming the Diagnosis column contains this information
       select(Sample_ID, Patient_Age, Gender, Diagnosis_Date) # Selecting the relevant columns

   # Remove duplicate sample IDs
   unique_samples <- liposarcoma_data %>%
       distinct(Sample_ID, .keep_all = TRUE)  # Keeping all metadata for unique sample IDs

   # Save the result to a CSV file
   output_file_path <- "/path/to/output/liposarcoma_unique_samples.csv"  # Update this path as needed
   write.csv(unique_samples, output_file_path, row.names = FALSE)  # Saving the unique samples data without row names