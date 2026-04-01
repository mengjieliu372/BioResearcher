exit <- function(code=0) quit(status=as.integer(code), save='no')
library(data.table)

kegg <- fread("/workspace/coding3/kegg_analysis_results.tsv")
kegg_top20 <- kegg[order(adj_p_value)][1:20]

fwrite(kegg_top20,
       "/workspace/coding3/kegg_top20_pathways.tsv",
       sep = "\t", quote = FALSE, na = "NA")