# filename: Part 1-dry-experiment-4.R
# This script installs FastQC and MultiQC, then performs quality control checks 
# on RNA-seq `.fastq` files and generates quality control reports.

# Define the working directory containing fastq files
working_dir <- "data"  # Modify if your fastq files are in a different directory

# Install FastQC and MultiQC
system("apt-get update")
system("apt-get install -y fastqc multiqc")

# Perform FastQC on all .fastq files in the working directory
system(paste("fastqc -o", working_dir, paste(working_dir, "*.fastq", sep="/")))

# Now, run MultiQC to generate a combined report
system(paste("multiqc", working_dir))

# Print completion message
print("Quality control checks completed. Reports generated.")