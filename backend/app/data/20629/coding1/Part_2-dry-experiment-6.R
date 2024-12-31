# filename: Part_2-dry-experiment-6.R
# This script validates findings using external datasets by replicating the chi-square, Kaplan-Meier, and Cox model analyses.

# Load necessary libraries
library(survival)
library(survminer)
library(dplyr)

# Load external dataset and metadata
# Assuming the datasets are pre-downloaded and named as 'expression_data.csv' and 'clinical_data.csv'
expression_data <- read.csv("data/expression_data.csv")
clinical_data <- read.csv("data/clinical_data.csv")

# Check the structure of the clinical data to identify survival time and status
print(str(clinical_data))

# Perform Chi-square tests for categorical variables
chi_square_results <- list()
for (var in names(clinical_data)[which(sapply(clinical_data, is.factor))]) {
  test_result <- chisq.test(table(clinical_data[[var]], clinical_data$case_status))
  chi_square_results[[var]] <- list(statistic = test_result$statistic, p.value = test_result$p.value)
}

# Save the Chi-square results
write.csv(do.call(rbind, lapply(chi_square_results, as.data.frame)), "data/chi_square_results.csv")

# Kaplan-Meier Survival Analysis
# Assuming 'survival_time' and 'survival_status' columns exist in the clinical data
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