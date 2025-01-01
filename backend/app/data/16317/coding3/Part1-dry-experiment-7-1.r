# List of directories to check
dirs_to_check <- c(
  "/path/to/output",           # Original path to check
  "/path/to/downloaded_data",  # Check if files are saved here
  "/path/to/another_directory"  # You can add more directories to check
)

# Loop through directories and list files
for (dir in dirs_to_check) {
  cat("Files in directory:", dir, "\n")
  files_list <- list.files(dir)
  print(files_list)
  cat("\n")  # Add spacing between directory results
}