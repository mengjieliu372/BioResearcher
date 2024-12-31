# filename: Part5-dry-experiment-3.R
# This script generates sample data for flow cytometry, IHC, and transcriptomic analyses,
# compares them, and outputs a comprehensive report summarizing the integrated analysis.

# Load necessary libraries
library(tidyverse)
library(readr)
library(knitr)
library(ggplot2)

# Generate sample data for Flow Cytometry analysis
flow_cytometry_data <- tibble(
  SampleID = 1:10,
  CD3_counts = rnorm(10, mean = 50, sd = 10),
  CD8_counts = rnorm(10, mean = 30, sd = 5)
)
write_csv(flow_cytometry_data, "data/flow_cytometry_analysis.csv")

# Generate sample data for IHC analysis
ihc_data <- tibble(
  SampleID = 1:10,
  IHC_staining_intensity = rnorm(10, mean = 100, sd = 15)
)
write_csv(ihc_data, "data/ihc_analysis.csv")

# Generate sample transcriptomic data
transcriptomic_data <- tibble(
  SampleID = 1:10,
  gene_expression = rnorm(10, mean = 200, sd = 30)
)
write_csv(transcriptomic_data, "data/transcriptomic_data.csv")

# Read the generated data files
flow_cytometry_data <- read_csv("data/flow_cytometry_analysis.csv")
ihc_data <- read_csv("data/ihc_analysis.csv")
transcriptomic_data <- read_csv("data/transcriptomic_data.csv")

# Basic data checks
print("Flow Cytometry Data Summary:")
print(summary(flow_cytometry_data))
print("IHC Data Summary:")
print(summary(ihc_data))
print("Transcriptomic Data Summary:")
print(summary(transcriptomic_data))

# Integrating datasets
integrated_data <- flow_cytometry_data %>%
  left_join(ihc_data, by = "SampleID") %>%
  left_join(transcriptomic_data, by = "SampleID")

# Validate findings by exploring correlations between datasets
correlation_results <- integrated_data %>%
  select(CD3_counts, IHC_staining_intensity, gene_expression) %>%
  cor(use = "complete.obs")

# Save correlation results
write_csv(as.data.frame(correlation_results), "data/correlation_results.csv")

# Create plots to visualize the relationships
ggplot(integrated_data, aes(x = gene_expression, y = CD3_counts)) +
  geom_point() +
  labs(title = "Correlation between Gene Expression and CD3 Counts",
       x = "Gene Expression",
       y = "CD3 Counts") +
  theme_minimal()

# Save the plot
ggsave("plots/gene_expression_vs_cd3_counts.png")

# Create a comprehensive report
report_summary <- paste(
  "This report summarizes the integrated analysis of flow cytometry, IHC, and transcriptomic data.",
  "The analysis validates immune cell populations and their molecular signatures.",
  "Key findings include correlations between immune markers and gene expression levels.")

# Save report summary to a text file
writeLines(report_summary, "data/comprehensive_report.txt")

# Final output messages
print("Correlation results saved to: data/correlation_results.csv")
print("Plot saved to: plots/gene_expression_vs_cd3_counts.png")
print("Comprehensive report saved to: data/comprehensive_report.txt")