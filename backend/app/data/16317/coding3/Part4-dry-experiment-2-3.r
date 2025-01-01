# Load the necessary package for KEGG analysis
library(clusterProfiler)

# Step 1: Read the DEGs input data containing gene identifiers and adjusted P-values
# Make sure to replace '/correct/path/to/differentially_expressed_genes.csv' with the actual file path
deg_data <- read.csv("/correct/path/to/differentially_expressed_genes.csv", header = TRUE)

# Step 2: Filter significant DEGs with an adjusted P-value < 0.05
significant_degs <- deg_data[deg_data$adj.P.Val < 0.05, c("gene_id", "adj.P.Val")]

# Step 3: Perform KEGG pathway analysis on the significant DEGs
kegg_results <- enrichKEGG(gene = significant_degs$gene_id, 
                            organism = "hsa",  # human
                            pvalueCutoff = 0.05)

# Step 4: Create data frame for pathways contained in results
kegg_summary <- data.frame(
  Pathway = kegg_results$Description,
  Gene_Count = kegg_results$Count,
  Adjusted_P_Value = kegg_results$p.adjust
)

# Step 5: Save the KEGG results as a tab-delimited file
# Ensure the output path is valid
write.table(kegg_summary, "/correct/path/to/output/kegg_pathway_analysis_results.tsv", 
            sep = "\t", row.names = FALSE, quote = FALSE)

# Print the results to verify
print(kegg_summary)