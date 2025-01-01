# Load necessary libraries (ensure the libraries are installed first)
library(DESeq2)
library(ggplot2)
library(pheatmap)
library(Rsamtools)
library(GenomicRanges)
library(GenomicFeatures)
library(txdbmaker)

# Set the file paths for BAM files (update these paths to where your BAM files are located)
bam_files <- c(
    "/path/to/downloaded_data/rna_seq/TCGA-LUAD_lncRNA_data.bam",
    "/path/to/downloaded_data/rna_seq/TCGA-PAAD_lncRNA_data.bam"
)

# Specify the correct path to the GTF file containing lncRNA annotations
gtf_file <- "/path/to/actual/path/to/gene_annotations.gtf" # Update this line accordingly

# Load GTF file and create a TxDb object using txdbmaker
# Ensure the GTF file exists at the specified location
if (!file.exists(gtf_file)) {
    stop("The specified GTF file does not exist. Please check the file path.")
}

txdb <- makeTxDbFromGFF(gtf_file, format="gtf")

# Define the GRanges for the lncRNA genes using the TxDb object
lncRNA_gr <- keys(txdb, keytype="GENEID")[allType(txdb) == "lncRNA"]

# Count raw reads
se <- summarizeOverlaps(features = lncRNA_gr, 
                         reads = bam_files, 
                         mode = "Union",
                         singleEnd = FALSE)

# Create DESeqDataSet object
colData <- data.frame(condition = factor(c("LUAD", "PAAD")))
dds <- DESeqDataSet(se, design = ~ condition)

# Proceed with analysis (normalize and perform differential expression analysis)
dds <- DESeq(dds)

# Extract results
results <- results(dds)

# Filter for significant lncRNAs
sig_results <- subset(results, padj < 0.05 & abs(log2FoldChange) > 1)

# Save significant results
write.csv(as.data.frame(sig_results), "/path/to/output/significant_lncRNAs.csv")

# Visualization: Volcano plot
volcano_data <- as.data.frame(sig_results)
ggplot(volcano_data, aes(x = log2FoldChange, y = -log10(padj))) +
    geom_point(aes(color = padj < 0.05), alpha = 0.5) +
    labs(title = "Volcano Plot of LncRNAs", x = "Log2 Fold Change", y = "-Log10 Adjusted p-value") +
    theme_minimal()
ggsave("/path/to/output/volcano_plot.png")

# Heatmap
significant_counts <- counts(dds)[rownames(sig_results), drop = FALSE]
pheatmap(significant_counts, cluster_rows = TRUE, cluster_cols = TRUE, filename = "/path/to/output/heatmap.png")

# Print summary of significant results
print(sig_results)