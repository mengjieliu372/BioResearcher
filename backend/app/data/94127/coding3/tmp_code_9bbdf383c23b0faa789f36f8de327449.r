exit <- function(code=0) quit(status=as.integer(code), save='no')
# Preview KEGG results
kegg <- data.table::fread("/workspace/coding3/kegg_analysis_results.tsv")
print(head(kegg))