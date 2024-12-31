# filename: Part_2_dry_experiment_3.R
# This script conducts Kaplan-Meier survival analysis to evaluate the prognostic significance of immunomolecular typing.
# It generates survival curves for different groups and performs log-rank tests.

# Load necessary libraries and install if not available
if (!requireNamespace("survival", quietly = TRUE)) {
    install.packages("survival")
}
if (!requireNamespace("survminer", quietly = TRUE)) {
    install.packages("survminer")
}
library(survival)
library(survminer)
library(dplyr)

# Define the data file path
data_file <- "data/survival_data.csv"  # Ensure this file exists and has the necessary columns

# Check if the file exists before proceeding
if (!file.exists(data_file)) {
    stop("The data file does not exist. Please ensure 'data/survival_data.csv' is available in the data directory.")
}

# Load the survival data
survival_data <- read.csv(data_file)

# Check the structure of the data
print(str(survival_data))

# Ensure the data frame has the necessary columns: 'time', 'status', 'immunotype'
if (!all(c("time", "status", "immunotype") %in% colnames(survival_data))) {
  stop("The data frame must include 'time', 'status', and 'immunotype' columns.")
}

# Fit Kaplan-Meier survival curves
km_fit <- survfit(Surv(time, status) ~ immunotype, data = survival_data)

# Plot the survival curves
ggsurvplot(km_fit, data = survival_data, 
           title = "Kaplan-Meier Survival Curves by Immunomolecular Typing",
           xlab = "Time",
           ylab = "Survival Probability",
           legend.title = "Immunomolecular Type",
           risk.table = TRUE)

# Perform log-rank test
log_rank_test <- survdiff(Surv(time, status) ~ immunotype, data = survival_data)
print(summary(log_rank_test))

# Save the plot
ggsave("Kaplan_Meier_Survival_Curves.png")