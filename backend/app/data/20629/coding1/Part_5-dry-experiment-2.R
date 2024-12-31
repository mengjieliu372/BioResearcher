# filename: Part_5-dry-experiment-2.R
# This script quantifies IHC staining intensity and distribution using ImageJ software,
# detailing specific plugins/tools used for analysis.

# This section installs necessary packages if they're not already installed.
if (!requireNamespace("rJava", quietly = TRUE)) {
    install.packages("rJava")
}

if (!requireNamespace("ggplot2", quietly = TRUE)) {
    install.packages("ggplot2")
}

library(rJava)
library(ggplot2)

# Set up ImageJ (ensure the path to ImageJ is correct)
imagej_path <- "path/to/ImageJ.jar"  # Adjust this path
.jinit(imagej_path)

# Function to analyze IHC staining intensity
analyze_ihc <- function(image_path) {
  message(paste("Processing:", image_path))
  result_list <- data.frame()  # Initialize empty data frame

  tryCatch({
    # Open image in ImageJ
    image_id <- .jcall("ij/ImagePlus", "I", "open", image_path)
    message("Image opened successfully.")
    
    # Convert to 8-bit
    .jcall("ij/process/ImageProcessor", "V", "convertToByte")
    message("Image converted to 8-bit.")
    
    # Apply threshold and analyze
    .jcall("ij/plugin/filter/ThresholdToSelection", "V", "run")
    message("Threshold applied.")
    
    # Run particle analysis
    res <- .jcall("ij/plugin/filter/ParticleAnalyzer", "Ljava/lang/Object;", "analyze", "size=100-Infinity display exclude")
    message("Particle analysis completed.")
    
    # Capture results
    result_table <- .jcall("ij/gui/ResultsTable", "Ljava/lang/Object;", "getTable")
    
    if (!is.null(result_table) && .jcall(result_table, "I", "getCounter") > 0) {
      result_list <- as.data.frame(result_table)
      message("Results obtained.")
    } else {
      message("No results returned from analysis.")
    }
    
  }, error = function(e) {
    message(paste("Error processing", image_path, ":", e$message))
  })

  return(result_list)
}

# List of TIFF image files in the specified directory
image_files <- list.files("path/to/your/tiff/images", pattern = "\\.tiff$", full.names = TRUE)

# Initialize a list to store results
ihc_results <- list()

# Analyze each image and store results
for (file in image_files) {
  ihc_results[[file]] <- analyze_ihc(file)
  print(ihc_results[[file]])  # Print results for each file
}

# Filter empty results
ihc_results <- Filter(function(x) !is.null(x) && nrow(x) > 0, ihc_results)

# Convert list of results to a data frame for further analysis
if (length(ihc_results) > 0) {
  ihc_summary <- do.call(rbind, lapply(ihc_results, function(x) as.data.frame(x)))
  
  # Generate heat map for IHC intensity distribution
  heatmap_data <- as.matrix(ihc_summary)
  ggplot(data = melt(heatmap_data), aes(Var1, Var2)) + 
    geom_tile(aes(fill = value)) + 
    scale_fill_gradient(low = "white", high = "red") +
    theme_minimal() +
    labs(x = "Image Files", y = "Intensity", fill = "Intensity Level") +
    ggtitle("IHC Staining Intensity Heat Map")
  ggsave("IHC_Staining_Heatmap.png")
  
  # Save summary results to a CSV file
  write.csv(ihc_summary, "IHC_Staining_Summary.csv", row.names = FALSE)
} else {
  message("No valid results found to generate heatmap or save summary.")
}