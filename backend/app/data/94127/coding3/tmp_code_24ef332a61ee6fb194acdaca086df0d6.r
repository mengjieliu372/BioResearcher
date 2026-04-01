exit <- function(code=0) quit(status=as.integer(code), save='no')
# Part5-dry-experiment-3-saved
# Kaplan–Meier survival analysis with high/low lncRNA expression (proxy if needed)

set.seed(1)
options(stringsAsFactors = FALSE)

suppressPackageStartupMessages({
  library(data.table)
})

log_file <- "/workspace/coding3/part5_dry_experiment_3_log.txt"
km_results_file <- "/workspace/coding3/part5_dry_experiment_3_km_results.csv"
km_plot_png <- "/workspace/coding3/part5_dry_experiment_3_km_plot.png"
km_plot_pdf <- "/workspace/coding3/part5_dry_experiment_3_km_plot.pdf"

cat(sprintf("Part 5-dry-experiment-3 started at: %s\n", Sys.time()),
    file = log_file)

# Inputs (allowlisted)
expr_file <- "/workspace/data/GSE202361_AllSamples_TPM.txt.gz"
meta_file <- "/workspace/data/GSE267611_sample_meta_out.txt.gz"

# Helper: safe write placeholder results
write_placeholder <- function(reason) {
  placeholder <- data.frame(
    gene = NA_character_,
    n_samples = 0,
    n_high = 0,
    n_low = 0,
    logrank_p = NA_real_,
    hazard_ratio = NA_real_,
    hr_ci_lower = NA_real_,
    hr_ci_upper = NA_real_,
    note = reason,
    stringsAsFactors = FALSE
  )
  fwrite(placeholder, km_results_file)
  # placeholder plot
  png(km_plot_png, width = 800, height = 600)
  plot.new()
  text(0.5, 0.5, labels = paste("KM plot unavailable:", reason))
  dev.off()
  pdf(km_plot_pdf, width = 8, height = 6)
  plot.new()
  text(0.5, 0.5, labels = paste("KM plot unavailable:", reason))
  dev.off()
  cat(sprintf("[WARN] %s\n", reason), file = log_file, append = TRUE)
}

# Load expression
expr_dt <- NULL
if (file.exists(expr_file)) {
  cat(sprintf("[INFO] Loading expression from: %s\n", expr_file),
      file = log_file, append = TRUE)
  expr_dt <- tryCatch(
    fread(expr_file),
    error = function(e) {
      cat(sprintf("[WARN] Failed to read expression: %s\n", e$message),
          file = log_file, append = TRUE)
      NULL
    }
  )
} else {
  cat(sprintf("[WARN] Expression file missing: %s\n", expr_file),
      file = log_file, append = TRUE)
}

if (is.null(expr_dt) || nrow(expr_dt) == 0 || ncol(expr_dt) < 3) {
  write_placeholder("Expression data missing or invalid")
} else {
  # Assume first column is gene ID; others are samples
  gene_col <- names(expr_dt)[1]
  expr_mat <- as.matrix(expr_dt[, -1, with = FALSE])
  rownames(expr_mat) <- expr_dt[[gene_col]]

  # Ensure numeric
  suppressWarnings(storage.mode(expr_mat) <- "numeric")

  # Pick top variable genes as proxy lncRNAs (no annotation provided)
  vars <- apply(expr_mat, 1, var, na.rm = TRUE)
  vars[is.na(vars)] <- 0
  top_genes <- names(sort(vars, decreasing = TRUE))[1:min(3, length(vars))]
  if (length(top_genes) == 0) {
    write_placeholder("No genes found after variance filtering")
  } else {
    cat(sprintf("[INFO] Using proxy lncRNA genes: %s\n",
                paste(top_genes, collapse = ", ")),
        file = log_file, append = TRUE)

    # Load survival metadata
    meta_dt <- NULL
    if (file.exists(meta_file)) {
      cat(sprintf("[INFO] Loading metadata from: %s\n", meta_file),
          file = log_file, append = TRUE)
      meta_dt <- tryCatch(
        fread(meta_file),
        error = function(e) {
          cat(sprintf("[WARN] Failed to read metadata: %s\n", e$message),
              file = log_file, append = TRUE)
          NULL
        }
      )
    } else {
      cat(sprintf("[WARN] Metadata file missing: %s\n", meta_file),
          file = log_file, append = TRUE)
    }

    # Try to find survival columns
    time_col <- event_col <- id_col <- NULL
    if (!is.null(meta_dt) && nrow(meta_dt) > 0) {
      cn <- names(meta_dt)
      time_candidates <- cn[grepl("time|days|os|survival", cn, ignore.case = TRUE)]
      event_candidates <- cn[grepl("event|status|dead|death", cn, ignore.case = TRUE)]
      id_candidates <- cn[grepl("sample|id", cn, ignore.case = TRUE)]

      time_col <- if (length(time_candidates) > 0) time_candidates[1] else NULL
      event_col <- if (length(event_candidates) > 0) event_candidates[1] else NULL
      id_col <- if (length(id_candidates) > 0) id_candidates[1] else NULL
    }

    if (is.null(meta_dt) || is.null(time_col) || is.null(event_col) || is.null(id_col)) {
      write_placeholder("Survival metadata missing required columns (time/event/sample_id)")
    } else {
      # Prepare survival data
      meta_dt <- as.data.frame(meta_dt)
      meta_dt$sample_id <- as.character(meta_dt[[id_col]])
      meta_dt$time <- suppressWarnings(as.numeric(meta_dt[[time_col]]))
      meta_dt$event <- suppressWarnings(as.numeric(meta_dt[[event_col]]))

      # Ensure event in {0,1}
      meta_dt$event <- ifelse(meta_dt$event > 1, 1, meta_dt$event)

      # Align samples
      expr_samples <- colnames(expr_mat)
      common_samples <- intersect(expr_samples, meta_dt$sample_id)

      if (length(common_samples) < 5) {
        write_placeholder("Insufficient overlapping samples between expression and survival data")
      } else {
        # Subset
        expr_sub <- expr_mat[, common_samples, drop = FALSE]
        meta_sub <- meta_dt[match(common_samples, meta_dt$sample_id), ]

        # Check survival validity
        if (all(is.na(meta_sub$time)) || all(is.na(meta_sub$event))) {
          write_placeholder("Survival time/event data are missing after alignment")
        } else {
          # Run KM for each proxy lncRNA
          if (!requireNamespace("survival", quietly = TRUE)) {
            write_placeholder("Package 'survival' not available")
          } else {
            library(survival)

            results_list <- list()
            plot_done <- FALSE

            for (g in top_genes) {
              expr_vec <- as.numeric(expr_sub[g, ])
              if (all(is.na(expr_vec))) next

              group <- ifelse(expr_vec >= median(expr_vec, na.rm = TRUE), "High", "Low")
              df <- data.frame(
                time = meta_sub$time,
                event = meta_sub$event,
                group = factor(group, levels = c("Low", "High"))
              )

              df <- df[!is.na(df$time) & !is.na(df$event), ]
              if (nrow(df) < 5 || length(unique(df$group)) < 2) next

              surv_obj <- Surv(time = df$time, event = df$event)
              fit <- survfit(surv_obj ~ group, data = df)

              # log-rank p-value
              sd <- survdiff(surv_obj ~ group, data = df)
              p_val <- 1 - pchisq(sd$chisq, df = length(sd$n) - 1)

              # hazard ratio
              hr <- hr_l <- hr_u <- NA_real_
              cox <- tryCatch(coxph(surv_obj ~ group, data = df), error = function(e) NULL)
              if (!is.null(cox)) {
                cox_sum <- summary(cox)
                hr <- cox_sum$coefficients[,"exp(coef)"][1]
                hr_l <- cox_sum$conf.int[,"lower .95"][1]
                hr_u <- cox_sum$conf.int[,"upper .95"][1]
              }

              results_list[[g]] <- data.frame(
                gene = g,
                n_samples = nrow(df),
                n_high = sum(df$group == "High"),
                n_low = sum(df$group == "Low"),
                logrank_p = p_val,
                hazard_ratio = hr,
                hr_ci_lower = hr_l,
                hr_ci_upper = hr_u,
                note = "Proxy lncRNA; based on top-variance genes",
                stringsAsFactors = FALSE
              )

              # Plot first gene
              if (!plot_done) {
                # Try survminer if available
                if (requireNamespace("survminer", quietly = TRUE)) {
                  suppressPackageStartupMessages(library(survminer))
                  p <- ggsurvplot(fit, data = df, pval = TRUE,
                                  title = paste("KM Survival:", g),
                                  risk.table = TRUE)
                  ggsave(km_plot_png, p$plot, width = 8, height = 6)
                  ggsave(km_plot_pdf, p$plot, width = 8, height = 6)
                } else {
                  png(km_plot_png, width = 800, height = 600)
                  plot(fit, col = c("blue", "red"), lwd = 2,
                       xlab = "Time", ylab = "Survival probability",
                       main = paste("KM Survival:", g))
                  legend("topright", legend = levels(df$group),
                         col = c("blue", "red"), lwd = 2)
                  dev.off()
                  pdf(km_plot_pdf, width = 8, height = 6)
                  plot(fit, col = c("blue", "red"), lwd = 2,
                       xlab = "Time", ylab = "Survival probability",
                       main = paste("KM Survival:", g))
                  legend("topright", legend = levels(df$group),
                         col = c("blue", "red"), lwd = 2)
                  dev.off()
                }
                plot_done <- TRUE
              }
            }

            if (length(results_list) == 0) {
              write_placeholder("KM analysis failed due to insufficient survival data after filtering")
            } else {
              res <- data.table::rbindlist(results_list, fill = TRUE)
              fwrite(res, km_results_file)
              cat(sprintf("[INFO] KM results saved: %s\n", km_results_file),
                  file = log_file, append = TRUE)
            }
          }
        }
      }
    }
  }
}

cat(sprintf("Part 5-dry-experiment-3 completed at: %s\n", Sys.time()),
    file = log_file, append = TRUE)