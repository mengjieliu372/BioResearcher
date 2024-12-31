# filename: Part_5_dry_experiment_1.R
# Task: Analyze flow cytometry data to confirm the presence and distribution of immune cells
# Input: Flow cytometry data files in FCS format located in 'data' directory
# Output: Graphs and tables of identified and quantified immune cell populations

# Load required libraries
if (!requireNamespace("flowCore", quietly = TRUE)) {
    install.packages("BiocManager")
    BiocManager::install("flowCore")
}
if (!requireNamespace("ggcyto", quietly = TRUE)) {
    BiocManager::install("ggcyto")
}

library(flowCore)
library(ggcyto)

# Set working directory
setwd("data")  # Assuming the FCS files are in 'data' directory

# List all FCS files in the directory
fcs_files <- list.files(pattern = "\\.fcs$", full.names = TRUE)

# Function to gate and analyze each FCS file
analyze_fcs <- function(fcs_file) {
    # Load FCS file
    fcs_data <- read.FCS(fcs_file)
    
    # Initialize a ggcyto object
    p <- ggcyto(fcs_data) +  
      geom_histogram(aes(x = `FL1.A`), bins = 30) +   # Plot 'FL1.A' channel
      labs(title = paste("Flow Cytometry Analysis for:", fcs_file))
    
    # Define gates for CD3, CD8, CD11c, and CD19
    # Example gates here (you might need to adjust the values accordingly)
    gating_criteria <- list(
        CD3 = list(x = 500, y = 2000),
        CD8 = list(x = 300, y = 2500),
        CD11c = list(x = 400, y = 1800),
        CD19 = list(x = 250, y = 2200)
    )
    
    # Create gates and calculate populations
    population_data <- data.frame(Population = character(), Count = numeric())
    
    for (cell_type in names(gating_criteria)) {
        gate <- gating_criteria[[cell_type]]
        g <- gate_2d(fcs_data, x = gate$x, y = gate$y)  # Gate based on criteria
        pop_count <- sum(g)  # Count cells in gate
        p <- p + geom_vline(xintercept = gate$x, linetype = "dashed", color = "red") + 
                 geom_hline(yintercept = gate$y, linetype = "dashed", color = "blue")
        population_data <- rbind(population_data, data.frame(Population = cell_type, Count = pop_count))
    }
    
    # Print summary table
    print(population_data)
    
    # Save plot
    ggsave(paste0("flow_analysis_", basename(fcs_file), ".png"), plot = p)
}

# Analyze each FCS file and save results
for (file in fcs_files) {
    analyze_fcs(file)
}
