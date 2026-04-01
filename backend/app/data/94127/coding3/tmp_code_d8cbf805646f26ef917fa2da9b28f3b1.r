exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part5-dry-experiment-2: lncRNA immune checkpoint expression analysis
# Uses only allowlisted inputs and writes outputs under /workspace/coding3

set.seed(1)
options(stringsAsFactors = FALSE)

suppressPackageStartupMessages({
  if (!requireNamespace("data.table", quietly = TRUE)) {
    install.packages("data.table", repos = "https://cloud.r-project.org")
  }
  library(data.table)
})

out_dir <- "/workspace/coding3"
log_file <- file.path(out_dir, "part5_dry_experiment_2_log.txt")

log_msg <- function(msg) {
  ts <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  cat(sprintf("[%s] %s\n", ts, msg), file = log_file, append = TRUE)
}

log_msg("Part 5-dry-experiment-2 started.")

# Allowlisted inputs
counts_file <- "/workspace/data/GSE202361_AllSamples_rawcount.txt.gz"
tpm_file    <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"

# Output files
de_all_file      <- file.path(out_dir, "part5_dry_experiment_2_de_results.csv")
de_sig_file      <- file.path(out_dir, "part5_dry_experiment_2_sig_lncrnas.csv")
corr_file        <- file.path(out_dir, "part5_dry_experiment_2_corr_matrix.csv")
heatmap_file     <- file.path(out_dir, "part5_dry_experiment_2_corr_heatmap.png")
volcano_file     <- file.path(out_dir, "part5_dry_experiment_2_volcano.png")

# Helper to read expression matrix
read_expr_matrix <- function(path) {
  if (!file.exists(path)) {
    log_msg(paste("WARNING: Missing file:", path))
    return(NULL)
  }
  dt <- tryCatch({
    data.table::fread(path)
  }, error = function(e) {
    log_msg(paste("WARNING: Failed to read:", path, "->", e$message))
    return(NULL)
  })
  if (is.null(dt) || nrow(dt) == 0 || ncol(dt) < 2) {
    log_msg(paste("WARNING: Empty/invalid matrix:", path))
    return(NULL)
  }
  # assume first column is gene ID
  gene_col <- names(dt)[1]
  mat <- as.matrix(dt[, -1, with = FALSE])
  rownames(mat) <- dt[[gene_col]]
  return(mat)
}

counts_mat <- read_expr_matrix(counts_file)
tpm_mat    <- read_expr_matrix(tpm_file)

if (is.null(counts_mat)) {
  # Placeholder outputs
  log_msg("No counts matrix available; writing placeholder outputs.")
  fwrite(data.table(gene=character(), log2FoldChange=numeric(),
                    pvalue=numeric(), padj=numeric(),
                    baseMean=numeric(), lncRNA_flag=logical()),
         de_all_file)
  fwrite(data.table(gene=character(), log2FoldChange=numeric(),
                    pvalue=numeric(), padj=numeric(),
                    baseMean=numeric()),
         de_sig_file)
  fwrite(data.table(), corr_file)
  png(heatmap_file, width=800, height=600)
  plot.new(); text(0.5, 0.5, "No data available for heatmap")
  dev.off()
  png(volcano_file, width=800, height=600)
  plot.new(); text(0.5, 0.5, "No data available for volcano plot")
  dev.off()
  log_msg("Part 5-dry-experiment-2 completed with placeholders.")
  quit(save = "no")
}

# Immune checkpoint gene list
checkpoint_genes <- c("PDCD1","CD274","PDCD1LG2","CTLA4","LAG3","TIGIT",
                      "HAVCR2","VSIR","BTLA","CD276","VTCN1","TNFRSF9",
                      "TNFRSF4","TNFRSF18","ICOS","IDO1","IDO2","CD70",
                      "CD80","CD86","CD40","TNFSF4","TNFSF18","TNFSF9")

# Determine which genes are present
gene_ids <- rownames(counts_mat)
present_checkpoints <- intersect(checkpoint_genes, gene_ids)

if (length(present_checkpoints) == 0) {
  log_msg("WARNING: No checkpoint genes found in matrix; using all genes for score proxy.")
  present_checkpoints <- gene_ids[seq_len(min(50, length(gene_ids)))]
}

# Compute checkpoint score to split samples into High/Low
score_mat <- counts_mat[present_checkpoints, , drop=FALSE]
checkpoint_score <- colMeans(log2(score_mat + 1), na.rm = TRUE)
group <- ifelse(checkpoint_score >= median(checkpoint_score, na.rm = TRUE), "High", "Low")
group <- factor(group, levels = c("Low","High"))

# Ensure at least 2 samples per group
if (min(table(group)) < 2) {
  log_msg("WARNING: Insufficient samples per group; creating random split.")
  group <- sample(rep(c("Low","High"), length.out = length(group)))
  group <- factor(group, levels = c("Low","High"))
}

# Differential expression using DESeq2 (preferred) or edgeR fallback
de_table <- NULL
if (requireNamespace("DESeq2", quietly = TRUE)) {
  suppressPackageStartupMessages(library(DESeq2))
  coldata <- data.frame(row.names = colnames(counts_mat), group = group)
  dds <- DESeqDataSetFromMatrix(countData = round(counts_mat),
                                colData = coldata,
                                design = ~ group)
  # minimal filtering
  keep <- rowSums(counts(dds)) > 1
  dds <- dds[keep, ]
  dds <- DESeq(dds, quiet = TRUE)
  res <- results(dds, contrast = c("group","High","Low"))
  de_table <- data.table(gene = rownames(res),
                         log2FoldChange = res$log2FoldChange,
                         pvalue = res$pvalue,
                         padj = res$padj,
                         baseMean = res$baseMean)
  log_msg("DESeq2 analysis completed.")
} else if (requireNamespace("edgeR", quietly = TRUE)) {
  suppressPackageStartupMessages(library(edgeR))
  group_vec <- group
  y <- DGEList(counts = counts_mat, group = group_vec)
  y <- calcNormFactors(y)
  design <- model.matrix(~ group_vec)
  y <- estimateDisp(y, design)
  fit <- glmQLFit(y, design)
  qlf <- glmQLFTest(fit, coef = 2)
  tab <- topTags(qlf, n = nrow(counts_mat))$table
  de_table <- data.table(gene = rownames(tab),
                         log2FoldChange = tab$logFC,
                         pvalue = tab$PValue,
                         padj = tab$FDR,
                         baseMean = tab$logCPM)
  log_msg("edgeR analysis completed.")
} else {
  log_msg("WARNING: Neither DESeq2 nor edgeR available; creating placeholder DE table.")
  de_table <- data.table(gene = gene_ids,
                         log2FoldChange = NA_real_,
                         pvalue = NA_real_,
                         padj = NA_real_,
                         baseMean = NA_real_)
}

# Identify lncRNAs (heuristic based on gene symbols)
is_ensembl <- mean(grepl("^ENSG", gene_ids)) > 0.8
if (is_ensembl) {
  log_msg("WARNING: Gene IDs appear to be Ensembl; lncRNA detection by symbol not possible. Marking all as non-lncRNA.")
  de_table[, lncRNA_flag := FALSE]
} else {
  lnc_regex <- paste(c("^LINC","^MIR","^AC[0-9]","^AL[0-9]","KCNQ1OT1",
                       "HOTAIR","MALAT1","NEAT1"), collapse="|")
  de_table[, lncRNA_flag := grepl(lnc_regex, gene)]
}

# Save all DE results
fwrite(de_table, de_all_file)

# Significant lncRNAs
sig_lncrna <- de_table[lncRNA_flag == TRUE &
                         !is.na(padj) & padj < 0.05 &
                         !is.na(log2FoldChange) & abs(log2FoldChange) > 1]

if (nrow(sig_lncrna) == 0) {
  log_msg("No significant lncRNAs found at specified thresholds.")
}
fwrite(sig_lncrna, de_sig_file)

# Correlation matrix between significant lncRNAs and checkpoint genes
if (!is.null(tpm_mat)) {
  corr_lncs <- intersect(sig_lncrna$gene, rownames(tpm_mat))
  corr_ckpt <- intersect(checkpoint_genes, rownames(tpm_mat))
  if (length(corr_lncs) > 0 && length(corr_ckpt) > 0) {
    expr_lncs <- tpm_mat[corr_lncs, , drop=FALSE]
    expr_ckpt <- tpm_mat[corr_ckpt, , drop=FALSE]
    corr_mat <- cor(t(expr_lncs), t(expr_ckpt), method = "pearson", use = "pairwise.complete.obs")
    fwrite(as.data.table(corr_mat, keep.rownames = "lncRNA"), corr_file)

    # Heatmap
    png(heatmap_file, width=1000, height=800)
    heatmap(corr_mat, Rowv = NA, Colv = NA, scale = "none",
            main = "lncRNA vs Immune Checkpoint Correlations",
            xlab = "Checkpoint genes", ylab = "lncRNAs")
    dev.off()
  } else {
    log_msg("WARNING: Insufficient genes for correlation heatmap; writing placeholder.")
    fwrite(data.table(), corr_file)
    png(heatmap_file, width=800, height=600)
    plot.new(); text(0.5, 0.5, "No correlation data available")
    dev.off()
  }
} else {
  log_msg("WARNING: TPM matrix missing; correlation heatmap not generated.")
  fwrite(data.table(), corr_file)
  png(heatmap_file, width=800, height=600)
  plot.new(); text(0.5, 0.5, "No TPM data available")
  dev.off()
}

# Volcano plot (lncRNAs only if available, otherwise all genes)
volcano_data <- if (any(de_table$lncRNA_flag, na.rm=TRUE)) {
  de_table[lncRNA_flag == TRUE]
} else {
  de_table
}

if (requireNamespace("ggplot2", quietly = TRUE) && nrow(volcano_data) > 0) {
  suppressPackageStartupMessages(library(ggplot2))
  volcano_data[, negLog10P := -log10(padj)]
  volcano_data[, sig := !is.na(padj) & padj < 0.05 & abs(log2FoldChange) > 1]

  p <- ggplot(volcano_data, aes(x = log2FoldChange, y = negLog10P)) +
    geom_point(aes(color = sig), alpha = 0.6) +
    scale_color_manual(values = c("grey70","red")) +
    theme_minimal() +
    labs(title = "Volcano Plot (lncRNAs)",
         x = "log2(Fold Change)", y = "-log10(adj P-value)")
  ggsave(volcano_file, plot = p, width = 7, height = 5, dpi = 150)
} else {
  png(volcano_file, width=800, height=600)
  plot.new(); text(0.5, 0.5, "Volcano plot unavailable")
  dev.off()
}

log_msg("Part 5-dry-experiment-2 completed.")