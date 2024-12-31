# filename: Part_4_dry_experiment_4.R
# This R script performs KEGG pathway enrichment analysis using the clusterProfiler package.
# It takes a gene list in TSV format for differentially expressed genes (DEGs) as input 
# and outputs enriched KEGG pathways with adjusted p-values < 0.05 in TSV format.

# Load necessary packages
if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager")
}
BiocManager::install("clusterProfiler", update = FALSE, ask = FALSE)

if (!requireNamespace("readr", quietly = TRUE)) {
  install.packages("readr")
}

library(clusterProfiler)
library(readr)

# Set input and output file paths
input_file <- "data/DEGs.tsv"  # Ensure this file exists in the 'data' directory
output_file <- "data/enriched_kegg_pathways.tsv"

# Check if input file exists
if (!file.exists(input_file)) {
  stop(paste("Input file does not exist:", input_file))
}

# Read the gene list
gene_list <- read_tsv(input_file, col_names = FALSE)[[1]]  # Assuming single column of gene symbols

# Perform KEGG enrichment analysis
kegg_result <- enrichKEGG(gene = gene_list, pAdjustMethod = "BH", pvalueCutoff = 0.05)

# Filter for significant pathways
significant_pathways <- kegg_result[kegg_result$p.adjust < 0.05, ]

# Save the results to a TSV file
write_tsv(as.data.frame(significant_pathways), output_file)

# Print summary of significant pathways
print(significant_pathways)