exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-4
# Apply limma::eBayes to fitted lmFit object with graceful fallbacks

suppressWarnings({
  options(stringsAsFactors = FALSE)
})

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

log_file <- file.path(out_dir, "part3_dry_experiment_4_ebayes_log.txt")
summary_csv <- file.path(out_dir, "part3_dry_experiment_4_ebayes_summary.csv")
top_csv <- file.path(out_dir, "part3_dry_experiment_4_topTable_all.csv")
rds_file <- file.path(out_dir, "part3_dry_experiment_4_ebayes_fit.rds")

write_log <- function(...) {
  msg <- paste0(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " | ", paste(..., collapse = ""))
  cat(msg, "\n")
  write(msg, file = log_file, append = TRUE)
}

# reset log
write("", file = log_file)

# Required package
if (!requireNamespace("limma", quietly = TRUE)) {
  write_log("WARNING: limma package not available. Writing placeholder outputs.")
  placeholder <- data.frame(
    metric = c("status", "reason"),
    value = c("placeholder", "limma_not_installed"),
    stringsAsFactors = FALSE
  )
  utils::write.csv(placeholder, summary_csv, row.names = FALSE)
  utils::write.csv(data.frame(), top_csv, row.names = FALSE)
  saveRDS(list(status = "placeholder", reason = "limma_not_installed"), rds_file)
} else {
  write_log("limma loaded successfully.")

  # Prefer concrete known lmFit output from prior step, then fallback candidates
  candidate_inputs <- c(
    file.path(out_dir, "part3_dry_experiment_3_lmfit.rds"),
    file.path(out_dir, "lmfit_fit.rds"),
    file.path(out_dir, "fitted_model.rds"),
    file.path(out_dir, "fit.rds")
  )
  existing_inputs <- candidate_inputs[file.exists(candidate_inputs)]

  if (length(existing_inputs) == 0) {
    write_log("WARNING: No lmFit RDS input found. Writing placeholder outputs.")
    placeholder <- data.frame(
      metric = c("status", "reason"),
      value = c("placeholder", "lmfit_input_missing"),
      stringsAsFactors = FALSE
    )
    utils::write.csv(placeholder, summary_csv, row.names = FALSE)
    utils::write.csv(data.frame(), top_csv, row.names = FALSE)
    saveRDS(list(status = "placeholder", reason = "lmfit_input_missing"), rds_file)
  } else {
    input_file <- existing_inputs[1]
    write_log("Using lmFit input: ", input_file)

    fit_obj <- tryCatch(readRDS(input_file), error = function(e) e)

    if (inherits(fit_obj, "error")) {
      write_log("WARNING: Failed to read lmFit object: ", conditionMessage(fit_obj))
      placeholder <- data.frame(
        metric = c("status", "reason"),
        value = c("placeholder", "lmfit_read_error"),
        stringsAsFactors = FALSE
      )
      utils::write.csv(placeholder, summary_csv, row.names = FALSE)
      utils::write.csv(data.frame(), top_csv, row.names = FALSE)
      saveRDS(list(status = "placeholder", reason = "lmfit_read_error"), rds_file)
    } else {
      # Apply eBayes
      ebayes_fit <- tryCatch(
        limma::eBayes(fit_obj),
        error = function(e) e
      )

      if (inherits(ebayes_fit, "error")) {
        write_log("WARNING: eBayes failed: ", conditionMessage(ebayes_fit))
        placeholder <- data.frame(
          metric = c("status", "reason"),
          value = c("placeholder", "ebayes_failed"),
          stringsAsFactors = FALSE
        )
        utils::write.csv(placeholder, summary_csv, row.names = FALSE)
        utils::write.csv(data.frame(), top_csv, row.names = FALSE)
        saveRDS(list(status = "placeholder", reason = "ebayes_failed"), rds_file)
      } else {
        write_log("eBayes completed successfully.")

        # Save eBayes object
        saveRDS(ebayes_fit, rds_file)

        # Build summary metrics
        n_genes <- if (!is.null(ebayes_fit$coefficients)) nrow(ebayes_fit$coefficients) else NA_integer_
        n_coef  <- if (!is.null(ebayes_fit$coefficients)) ncol(ebayes_fit$coefficients) else NA_integer_
        df_prior <- if (!is.null(ebayes_fit$df.prior)) paste(ebayes_fit$df.prior, collapse = ";") else NA_character_
        s2_prior <- if (!is.null(ebayes_fit$s2.prior)) paste(ebayes_fit$s2.prior, collapse = ";") else NA_character_

        summary_df <- data.frame(
          metric = c("status", "input_file", "n_genes", "n_coefficients", "df_prior", "s2_prior"),
          value = c("ok", input_file, n_genes, n_coef, df_prior, s2_prior),
          stringsAsFactors = FALSE
        )
        utils::write.csv(summary_df, summary_csv, row.names = FALSE)

        # Export full topTable for first coefficient (common downstream contract)
        tt <- tryCatch(
          limma::topTable(ebayes_fit, coef = 1, number = Inf, sort.by = "P"),
          error = function(e) e
        )

        if (inherits(tt, "error")) {
          write_log("WARNING: topTable extraction failed: ", conditionMessage(tt))
          utils::write.csv(data.frame(), top_csv, row.names = FALSE)
        } else {
          tt_out <- data.frame(gene_id = rownames(tt), tt, check.names = FALSE)
          rownames(tt_out) <- NULL
          utils::write.csv(tt_out, top_csv, row.names = FALSE)
          write_log("topTable exported: ", top_csv, " (rows=", nrow(tt_out), ").")
        }

        write_log("Outputs written: ", summary_csv, ", ", top_csv, ", ", rds_file)
      }
    }
  }
}