# filename: generate_sample_survival_data.R
# This script generates a sample survival data frame and writes it to a CSV file for testing.

# Load necessary libraries
set.seed(123)  # For reproducibility

# Generate sample data
n <- 100  # Number of samples
survival_data <- data.frame(
    time = rexp(n, rate = 0.1),  # Random survival times
    status = sample(0:1, n, replace = TRUE),  # Randomly 0 (censored) or 1 (event)
    immunotype = sample(c("TypeA", "TypeB", "TypeC"), n, replace = TRUE)  # Random immunotype groups
)

# Write to a CSV file
write.csv(survival_data, "data/survival_data.csv", row.names = FALSE)
print("Sample survival data generated and saved as 'data/survival_data.csv'.")