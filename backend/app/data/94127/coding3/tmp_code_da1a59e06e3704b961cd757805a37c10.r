exit <- function(code=0) quit(status=as.integer(code), save='no')
library(data.table)
library(ggplot2)

kegg <- fread("/workspace/coding3/kegg_analysis_results.tsv")
kegg_top20 <- kegg[order(adj_p_value)][1:20]

# For plotting, order pathways by significance
kegg_top20[, pathway_name := factor(pathway_name, levels = rev(kegg_top20$pathway_name))]

p <- ggplot(kegg_top20, aes(x = pathway_name, y = -log10(adj_p_value), fill = gene_count)) +
  geom_bar(stat = "identity") +
  coord_flip() +
  theme_minimal(base_size = 12) +
  labs(title = "Top 20 KEGG Pathways",
       x = "Pathway",
       y = "-log10(adj p-value)",
       fill = "Gene Count")

ggsave("/workspace/coding3/kegg_top20_barplot.png", p, width = 8, height = 6)