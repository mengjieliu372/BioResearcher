# filename: Part 1-dry-experiment-4-file-check.R
# This script checks the contents of the data directory to list .fastq files.

# Define the working directory containing fastq files
working_dir <- "data"  # Modify if your fastq files are in a different directory

# List the contents of the working directory
files <- list.files(path = working_dir, pattern = "*.fastq", full.names = TRUE)

# Print the list of .fastq files found
if(length(files) > 0) {
  print("Found .fastq files:")
  print(files)
} else {
  print("No .fastq files found in the specified directory.")
}