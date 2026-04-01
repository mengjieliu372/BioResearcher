exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-4: Apply eBayes to fitted limma model
# Output: eBayes object (RDS), summary statistics CSV, and log
# Constraints: graceful handling if input missing; no stop/quit; outputs under /workspace/coding3

suppressPackageStartupMessages({
  library(limma)
  library(data.table)
})

output_dir <- "/workspace/coding3"
ebayes_rds <- file.path(output_dir, "ebayes_fit.rds")
ebayes_csv <- file.path(output_dir, "ebayes_statistics.csv")
log_file   <- file.path(output_dir, "ebayes_log.txt")

# Candidate paths for lmFit object from previous step (no directory scanning)
candidate_fit_paths <- c(
  file.path(output_dir, "limma_fit.rds"),
  file.path(output_dir, "lmfit_fit.rds"),
  file.path(output_dir, "lmfit_model.rds"),
  file.path(output_dir, "part3_dry_experiment_3_fit.rds")
)

fit_path <- NA_character_
for (p in candidate_fit_paths) {
  if (file.exists(p)) {
    fit_path <- p
    break
  }
}

log_lines <- c(sprintf("Part 3-dry-experiment-4 started at %s", Sys.time()))

if (is.na(fit_path)) {
  warning("No fitted lmFit object found in /workspace/coding3. Creating placeholder outputs.")
  log_lines <- c(log_lines, "WARNING: No fitted lmFit object found; placeholder outputs created.")
  
  # Placeholder object and table
  placeholder_obj <- list(
    error = "Missing lmFit object",
    message = "No fitted model found in /workspace/coding3; eBayes not computed.",
    timestamp = Sys.time()
  )
  saveRDS(placeholder_obj, ebayes_rds)
  
  placeholder_df <- data.frame(
    gene_id = NA_character_,
    coefficient = NA_character_,
    logFC = NA_real_,
    t = NA_real_,
    P.Value = NA_real_,
    adj.P.Val = NA_real_,
    B = NA_real_,
    note = "Placeholder: missing lmFit object"
  )
  fwrite(placeholder_df, ebayes_csv)
  
} else {
  log_lines <- c(log_lines, paste("Found fitted model at:", fit_path))
  
  # Load and run eBayes safely
  fit_obj <- NULL
  ebayes_obj <- NULL
  
  fit_obj <- tryCatch(readRDS(fit_path), error = function(e) e)
  if (inherits(fit_obj, "error")) {
    warning("Failed to read fitted model RDS; creating placeholder outputs.")
    log_lines <- c(log_lines, paste("ERROR reading fit object:", fit_obj$message))
    
    placeholder_obj <- list(
      error = "Failed to read lmFit object",
      message = fit_obj$message,
      timestamp = Sys.time()
    )
    saveRDS(placeholder_obj, ebayes_rds)
    
    placeholder_df <- data.frame(
      gene_id = NA_character_,
      coefficient = NA_character_,
      logFC = NA_real_,
      t = NA_real_,
      P.Value = NA_real_,
      adj.P.Val = NA_real_,
      B = NA_real_,
      note = "Placeholder: failed to read lmFit object"
    )
    fwrite(placeholder_df, ebayes_csv)
    
  } else {
    # Apply eBayes
    ebayes_obj <- tryCatch(eBayes(fit_obj), error = function(e) e)
    
    if (inherits(ebayes_obj, "error")) {
      warning("eBayes failed; creating placeholder outputs.")
      log_lines <- c(log_lines, paste("ERROR running eBayes:", ebayes_obj$message))
      
      placeholder_obj <- list(
        error = "eBayes failed",
        message = ebayes_obj$message,
        timestamp = Sys.time()
      )
      saveRDS(placeholder_obj, ebayes_rds)
      
      placeholder_df <- data.frame(
        gene_id = NA_character_,
        coefficient = NA_character_,
        logFC = NA_real_,
        t = NA_real_,
        P.Value = NA_real_,
        adj.P.Val = NA_real_,
        B = NA_real_,
        note = "Placeholder: eBayes failed"
      )
      fwrite(placeholder_df, ebayes_csv)
      
    } else {
      # Save eBayes object
      saveRDS(ebayes_obj, ebayes_rds)
      
      # Build summary statistics table
      coefs <- ebayes_obj$coefficients
      tstats <- ebayes_obj$t
      pvals <- ebayes_obj$p.value
      lods <- ebayes_obj$lods
      
      coef_names <- colnames(coefs)
      if (is.null(coef_names)) coef_names <- paste0("coef", seq_len(ncol(coefs)))
      
      gene_ids <- rownames(coefs)
      if (is.null(gene_ids)) gene_ids <- paste0("gene_", seq_len(nrow(coefs)))
      
      stats_list <- lapply(seq_along(coef_names), function(i) {
        data.frame(
          gene_id = gene_ids,
          coefficient = coef_names[i],
          logFC = coefs[, i],
          t = tstats[, i],
          P.Value = pvals[, i],
          adj.P.Val = p.adjust(pvals[, i], method = "BH"),
          B = lods[, i],
          stringsAsFactors = FALSE
        )
      })
      
      stats_df <- rbindlist(stats_list, fill = TRUE)
      fwrite(stats_df, ebayes_csv)
      
      log_lines <- c(log_lines, "eBayes completed successfully.")
    }
  }
}

log_lines <- c(log_lines, sprintf("Completed at %s", Sys.time()))
writeLines(log_lines, log_file)