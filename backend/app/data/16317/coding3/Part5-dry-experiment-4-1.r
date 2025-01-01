# Load necessary library
library(fs)

# Specify the output directory
output_directory <- "/path/to/output/"  # Update this to your actual output directory

# List files in the output directory
files_in_directory <- dir_ls(output_directory)

# Print the files
print("Files in the output directory:")
print(files_in_directory)