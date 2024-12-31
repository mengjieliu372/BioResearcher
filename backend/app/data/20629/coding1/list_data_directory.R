# filename: list_data_directory.R
# This script lists the contents of the 'data' directory to check for the input files.

# Set the path to the data directory
data_directory <- "data"

# List the files in the data directory
files_in_data <- list.files(data_directory)

# Print the files
print(files_in_data)