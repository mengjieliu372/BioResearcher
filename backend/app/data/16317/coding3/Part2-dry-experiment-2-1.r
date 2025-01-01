# Check if the 'ShortRead' package is installed and install if not
if (!requireNamespace("ShortRead", quietly = TRUE)) {
  install.packages("BiocManager")
  BiocManager::install("ShortRead")
}

# Load necessary libraries
library(ShortRead)   # For reading RNA sequencing data
library(ggplot2)     # For plotting
library(dplyr)       # For data manipulation

# Define file paths
rna_seq_files <- list.files("/path/to/downloaded_data/rna_seq", pattern = "*.txt", full.names = TRUE)
qc_report_path <- "/path/to/output/qc_report.csv"
degradation_plot_path <- "/path/to/output/rna_degradation_plot.png"

# Initialize an empty data frame for QC results
qc_results <- data.frame(SampleID = character(),
                         PassFail = character(),
                         Ratio = numeric(),
                         stringsAsFactors = FALSE)

# Perform quality control
for (file in rna_seq_files) {
  # Load the RNA sequencing data
  data <- read.table(file, header = TRUE, row.names = 1)

  # Check for presence of 3p and 5p columns or simulate RAtion calculation
  if ("3p" %in% colnames(data) && "5p" %in% colnames(data)) {
    ratio <- rowMeans(data[,"3p"], na.rm = TRUE) / rowMeans(data[,"5p"], na.rm = TRUE)
    pass_fail <- ifelse(ratio > 1.5, "Pass", "Fail")
    
    # Store results in qc_results
    qc_results <- rbind(qc_results, data.frame(SampleID = basename(file),
                                                 PassFail = pass_fail,
                                                 Ratio = ratio))
  } else {
    # If 3p and 5p data is not present, log sample as excluded
    qc_results <- rbind(qc_results, data.frame(SampleID = basename(file),
                                                 PassFail = "Excluded",
                                                 Ratio = NA))
  }
}

# Generate degradation plots if there are any samples
if (nrow(qc_results) > 0) {
  plot <- ggplot(qc_results, aes(x = SampleID, y = Ratio, fill = PassFail)) +
    geom_bar(stat = "identity", na.rm = TRUE) +
    theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
    labs(title = "RNA Degradation Analysis", x = "Sample ID", y = "3'/5' Ratio")
  
  ggsave(degradation_plot_path, plot)
}

# Save QC report
write.csv(qc_results, qc_report_path, row.names = FALSE)

# Print success messages
print(paste("Quality control report saved to:", qc_report_path))
print(paste("RNA degradation plot saved to:", degradation_plot_path))