# Load necessary library for GO enrichment analysis
if (!requireNamespace("clusterProfiler", quietly = TRUE)) {
  install.packages("BiocManager")
  BiocManager::install("clusterProfiler")
}

library(clusterProfiler)

# Step: Debug - List all files under '/path/to/downloaded_data/' to find any CSV files
print(list.files(path = '/path/to/downloaded_data', pattern = "*.csv", full.names = TRUE, recursive = TRUE))  # Look specifically for CSV files

# Step: List all files to get an overview
print(list.files(path = '/path/to/downloaded_data', full.names = TRUE, recursive = TRUE))

# Update deg_file with the correct name after you find your file
# this should point to your significant DEGs data
deg_file <- '/path/to/downloaded_data/your_correct_file_name.csv'  # Correct this after listing files

# Read the input data containing significant DEGs
deg_data <- read.csv(deg_file)

# Check if the necessary columns exist
if (!all(c("gene_id", "adjusted_p_value") %in% colnames(deg_data))) {
  stop("The input data must contain 'gene_id' and 'adjusted_p_value' columns.")
}

# Filter significant DEGs based on adjusted P-value < 0.05
significant_degs <- deg_data[deg_data$adjusted_p_value < 0.05, 'gene_id']

# Step 2: Conduct GO enrichment analysis
go_results <- enrichGO(gene = significant_degs,
                       OrgDb = "org.Hs.eg.db", 
                       keyType = "SYMBOL",  
                       ont = "BP",  
                       pAdjustMethod = "BH",
                       qvalueCutoff = 0.05,
                       readable = TRUE)

# Step 3: Format results
go_df <- as.data.frame(go_results)
go_df <- go_df[, c("ID", "Description", "Count", "p.adjust")]
colnames(go_df) <- c("GO_Term", "Description", "Gene_Count", "Adjusted_P_Value")

# Step 4: Save results to a CSV file
output_file <- '/path/to/output/go_enrichment_results.csv'  # Adjust this path accordingly
write.csv(go_df, file = output_file, row.names = FALSE)

# Print the results to confirm successful execution
print(go_df)