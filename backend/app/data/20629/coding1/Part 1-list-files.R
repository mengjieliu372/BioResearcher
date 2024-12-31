# filename: Part 1-list-files.R
# This script lists all files in the current working directory to help you identify the correct input file.
# Output: List of files in the current working directory.

# List files in the current working directory
files <- list.files()
print("Files in the current working directory:")
print(files)