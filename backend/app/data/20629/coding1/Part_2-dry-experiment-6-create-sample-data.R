# filename: Part_2-dry-experiment-6-create-sample-data.R
# This script creates sample data if necessary input files do not exist and then validates findings through chi-square, Kaplan-Meier, and Cox model analyses.

# Load necessary libraries
library(survival)
library(survminer)
library(dplyr)

# Define file paths
expression_data_path <- "data/expression_data.csv"
clinical_data_path <- "data/clinical_data.csv"

# Create sample data if files do not exist
if (!file.exists(expression_data_path)) {
  cat("Creating sample expression data...\n")
  expression_data <- data.frame(Gene = paste0("Gene", 1:100),
                                 Expression = rnorm(100, mean = 10, sd = 5))
  write.csv(expression_data, expression_data_path, row.names = FALSE)
}

if (!file.exists(clinical_data_path)) {
  cat("Creating sample clinical data...\n")
  set.seed(42)
  clinical_data <- data.frame(survival_time = rexp(100, rate = 0.1),
                               survival_status = sample(0:1, 100, replace = TRUE),
                               case_status = sample(c("Group1", "Group2"), 100, replace = TRUE),
                               age = sample(30:80, 100, replace = TRUE),
                               gender = sample(c("Male", "Female"), 100, replace = TRUE))
  write.csv(clinical_data, clinical_data_path, row.names = FALSE)
}

# Load datasets
expression_data <- read.csv(expression_data_path)
clinical_data <- read.csv(clinical_data_path)

# Perform Chi-square tests for categorical variables
chi_square_results <- list()
for (var in names(clinical_data)[which(sapply(clinical_data, is.factor))]) {
  test_result <- chisq.test(table(clinical_data[[var]], clinical_data$case_status))
  chi_square_results[[var]] <- list(statistic = test_result$statistic, p.value = test_result$p.value)
}

# Save the Chi-square results
write.csv(do.call(rbind, lapply(chi_square_results, as.data.frame)), "data/chi_square_results.csv")

# Kaplan-Meier Survival Analysis
km_fit <- survfit(Surv(survival_time, survival_status) ~ case_status, data = clinical_data)
ggsurv <- ggsurvplot(km_fit, data = clinical_data, risk.table = TRUE, pval = TRUE)
print(ggsurv)

# Save the Kaplan-Meier plot
ggsave("data/kapsurvival_plot.png", plot = ggsurv$plot)

# Cox Proportional Hazards Model
cox_fit <- coxph(Surv(survival_time, survival_status) ~ case_status + age + gender, data = clinical_data)

# Summary of Cox model
cox_summary <- summary(cox_fit)
write.csv(data.frame(cox_summary$coefficients), "data/cox_model_results.csv")

# Output Cox model diagnostics (e.g., hazard ratios, confidence intervals)
print(cox_summary)

# The validation results are saved for review