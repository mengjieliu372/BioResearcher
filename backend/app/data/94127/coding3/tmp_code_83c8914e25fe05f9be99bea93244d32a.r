exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part 3-dry-experiment-4 (corrected)
# Goal: obtain lmFit object robustly, then run limma::eBayes

suppressWarnings(options(stringsAsFactors = FALSE))

out_dir <- "/workspace/coding3"
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

log_file    <- file.path(out_dir, "part3_dry_experiment_4_ebayes_log.txt")
summary_csv <- file.path(out_dir, "part3_dry_experiment_4_ebayes_summary.csv")
top_csv     <- file.path(out_dir, "part3_dry_experiment_4_topTable_all.csv")
ebayes_rds  <- file.path(out_dir, "part3_dry_experiment_4_ebayes_fit.rds")

write("", file = log_file)

log_msg <- function(...) {
  msg <- paste0(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " | ", paste(..., collapse = ""))
  cat(msg, "\n")
  write(msg, file = log_file, append = TRUE)
}

write_placeholder <- function(reason) {
  utils::write.csv(
    data.frame(metric = c("status", "reason"), value = c("placeholder", reason)),
    summary_csv, row.names = FALSE
  )
  utils::write.csv(data.frame(), top_csv, row.names = FALSE)
  saveRDS(list(status = "placeholder", reason = reason), ebayes_rds)
}

if (!requireNamespace("limma", quietly = TRUE)) {
  log_msg("WARNING: limma not installed.")
  write_placeholder("limma_not_installed")
} else {

  fit_obj <- NULL

  # 1) Try direct lmFit RDS candidates from previous step
  lmfit_candidates <- c(
    file.path(out_dir, "part3_dry_experiment_3_lmfit.rds"),
    file.path(out_dir, "lmfit_fit.rds"),
    file.path(out_dir, "fitted_model.rds"),
    file.path(out_dir, "fit.rds")
  )
  existing_lmfit <- lmfit_candidates[file.exists(lmfit_candidates)]

  if (length(existing_lmfit) > 0) {
    fit_try <- tryCatch(readRDS(existing_lmfit[1]), error = function(e) e)
    if (!inherits(fit_try, "error")) {
      fit_obj <- fit_try
      log_msg("Loaded lmFit object from: ", existing_lmfit[1])
    } else {
      log_msg("WARNING: Failed reading direct lmFit RDS: ", conditionMessage(fit_try))
    }
  } else {
    log_msg("No direct lmFit RDS found; attempting recovery from known prior outputs.")
  }

  # 2) Try extracting lmFit-like object from rnaseq_loaded_objects.rds
  if (is.null(fit_obj)) {
    loaded_obj_file <- file.path(out_dir, "rnaseq_loaded_objects.rds")
    if (file.exists(loaded_obj_file)) {
      obj <- tryCatch(readRDS(loaded_obj_file), error = function(e) e)
      if (!inherits(obj, "error")) {
        # check top-level
        if (inherits(obj, "MArrayLM")) {
          fit_obj <- obj
          log_msg("Recovered lmFit object directly from rnaseq_loaded_objects.rds.")
        } else if (is.list(obj)) {
          # search common names
          name_priority <- c("fit", "lmfit", "lmFit", "fitted_model", "model_fit")
          found_name <- name_priority[name_priority %in% names(obj)]
          if (length(found_name) > 0 && inherits(obj[[found_name[1]]], "MArrayLM")) {
            fit_obj <- obj[[found_name[1]]]
            log_msg("Recovered lmFit object from rnaseq_loaded_objects.rds$", found_name[1])
          } else {
            # generic class-based search in list elements
            idx <- which(vapply(obj, function(x) inherits(x, "MArrayLM"), logical(1)))
            if (length(idx) > 0) {
              fit_obj <- obj[[idx[1]]]
              log_msg("Recovered lmFit object from rnaseq_loaded_objects.rds list element: ", names(obj)[idx[1]])
            }
          }
        }
      } else {
        log_msg("WARNING: Could not read rnaseq_loaded_objects.rds: ", conditionMessage(obj))
      }
    } else {
      log_msg("rnaseq_loaded_objects.rds not found.")
    }
  }

  # 3) Last resort: rebuild lmFit from known loaded matrices + design_matrix.rds
  if (is.null(fit_obj)) {
    design_file <- file.path(out_dir, "design_matrix.rds")
    tpm_file    <- file.path(out_dir, "gse202361_tpm_loaded.csv")
    cnt_file    <- file.path(out_dir, "gse202361_counts_loaded.csv")

    if (file.exists(design_file) && (file.exists(cnt_file) || file.exists(tpm_file))) {
      design <- tryCatch(readRDS(design_file), error = function(e) e)
      if (!inherits(design, "error") && is.matrix(design)) {
        expr <- NULL

        # Prefer counts if numeric and matrix-like, otherwise TPM
        if (file.exists(cnt_file)) {
          cnt <- tryCatch(utils::read.csv(cnt_file, check.names = FALSE), error = function(e) e)
          if (!inherits(cnt, "error") && ncol(cnt) >= 2) {
            # assume first column is gene id
            mat <- as.matrix(cnt[, -1, drop = FALSE])
            suppressWarnings(storage.mode(mat) <- "numeric")
            rownames(mat) <- cnt[[1]]
            expr <- mat
            log_msg("Using counts matrix for refit: ", cnt_file)
          }
        }
        if (is.null(expr) && file.exists(tpm_file)) {
          tpm <- tryCatch(utils::read.csv(tpm_file, check.names = FALSE), error = function(e) e)
          if (!inherits(tpm, "error") && ncol(tpm) >= 2) {
            mat <- as.matrix(tpm[, -1, drop = FALSE])
            suppressWarnings(storage.mode(mat) <- "numeric")
            rownames(mat) <- tpm[[1]]
            expr <- mat
            log_msg("Using TPM matrix for refit: ", tpm_file)
          }
        }

        if (!is.null(expr)) {
          common <- intersect(colnames(expr), rownames(design))
          if (length(common) >= 2) {
            expr2 <- expr[, common, drop = FALSE]
            design2 <- design[common, , drop = FALSE]
            fit_try <- tryCatch(limma::lmFit(expr2, design2), error = function(e) e)
            if (!inherits(fit_try, "error")) {
              fit_obj <- fit_try
              log_msg("Successfully rebuilt lmFit from loaded expression + design matrix.")
            } else {
              log_msg("WARNING: Rebuilding lmFit failed: ", conditionMessage(fit_try))
            }
          } else {
            log_msg("WARNING: No sufficient overlapping samples between expression and design.")
          }
        }
      } else {
        log_msg("WARNING: design_matrix.rds missing or unreadable as matrix.")
      }
    } else {
      log_msg("Insufficient files for rebuild fallback.")
    }
  }

  # 4) eBayes if fit available
  if (is.null(fit_obj)) {
    log_msg("WARNING: No usable lmFit object found after all fallbacks.")
    write_placeholder("lmfit_unavailable_after_fallbacks")
  } else {
    eb <- tryCatch(limma::eBayes(fit_obj), error = function(e) e)
    if (inherits(eb, "error")) {
      log_msg("WARNING: eBayes failed: ", conditionMessage(eb))
      write_placeholder("ebayes_failed")
    } else {
      saveRDS(eb, ebayes_rds)

      n_genes <- if (!is.null(eb$coefficients)) nrow(eb$coefficients) else NA_integer_
      n_coef  <- if (!is.null(eb$coefficients)) ncol(eb$coefficients) else NA_integer_

      utils::write.csv(
        data.frame(
          metric = c("status", "n_genes", "n_coefficients", "df_prior", "s2_prior"),
          value = c(
            "ok",
            n_genes,
            n_coef,
            if (!is.null(eb$df.prior)) paste(eb$df.prior, collapse = ";") else NA_character_,
            if (!is.null(eb$s2.prior)) paste(eb$s2.prior, collapse = ";") else NA_character_
          ),
          stringsAsFactors = FALSE
        ),
        summary_csv,
        row.names = FALSE
      )

      tt <- tryCatch(limma::topTable(eb, coef = 1, number = Inf, sort.by = "P"), error = function(e) e)
      if (inherits(tt, "error")) {
        log_msg("WARNING: topTable failed: ", conditionMessage(tt))
        utils::write.csv(data.frame(), top_csv, row.names = FALSE)
      } else {
        tt_out <- data.frame(gene_id = rownames(tt), tt, check.names = FALSE)
        rownames(tt_out) <- NULL
        utils::write.csv(tt_out, top_csv, row.names = FALSE)
        log_msg("eBayes completed successfully; topTable rows: ", nrow(tt_out))
      }
    }
  }
}