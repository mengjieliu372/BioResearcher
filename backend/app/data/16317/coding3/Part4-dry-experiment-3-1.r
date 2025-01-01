# Load necessary libraries
library(clusterProfiler)  # For GO analysis
library(DOSE)             # For KEGG analysis

# Example of performing GO enrichment analysis
gene_list <- c("Gene1", "Gene2", "Gene3")  # Replace with your actual genes of interest

# Perform GO analysis
go_results <- enrichGO(gene     = gene_list,
                        OrgDb    = org.Hs.eg.db,
                        keyType  = "SYMBOL",
                        ont      = "BP", 
                        pAdjustMethod = "BH",
                        qvalueCutoff = 0.05)

write.csv(as.data.frame(go_results), "/path/to/output/go_analysis_results.csv")  # Save results

# Perform KEGG analysis
kegg_results <- enrichKEGG(gene = gene_list, organism = 'hsa', pAdjustMethod = "BH")

write.table(as.data.frame(kegg_results), "/path/to/output/kegg_pathway_analysis_results.tsv", sep = "\t", row.names = FALSE, quote = FALSE)  # Save results