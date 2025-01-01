# Load necessary libraries for making HTTP requests to GDC API
library(httr)
library(jsonlite)

# Define the project IDs for TCGA-LUAD and TCGA-PAAD
project_ids <- c("TCGA-LUAD", "TCGA-PAAD")

# Define the immune checkpoint molecules of interest
target_genes <- c("PDCD1", "CD274", "CTLA4")

# Function to query GDC for RNA sequencing data
query_gdc <- function(project_id) {
  # Create the request body for the POST API call
  query_body <- list(
    filters = list(
      "op" = "and",
      "content" = list(
        list(
          "op" = "=",
          "content" = list(
            "field" = "project.project_id",
            "value" = project_id
          )
        ),
        list(
          "op" = "in",
          "content" = list(
            "field" = "files.file_name",
            "value" = target_genes
          )
        )
      )
    ),
    fields = c("file_id", "file_name", "cases", "metadata"),
    format = "json", # Request format
    size = 1000 # Adjust size if necessary
  )
  
  # Send POST request to GDC API
  response <- POST(
    url = "https://api.gdc.cancer.gov/data",
    body = toJSON(query_body),
    encode = "json",
    add_headers(`Content-Type` = "application/json")
  )
  
  # Check if the request was successful
  if (http_status(response)$category == "Success") {
    return(content(response, "parsed"))
  } else {
    stop("Error querying GDC: ", http_status(response)$message)
  }
}

# Function to download RNA sequencing datasets
download_gdc_data <- function(project_id) {
  # Obtain the data associated with the project
  data_info <- query_gdc(project_id)
  
  # Download data (you'll need to adapt the download process for the specific fields)
  for (data in data_info$data) {
    file_id <- data$file_id
    download_url <- sprintf("https://gdc.cancer.gov/api/v0/data/%s", file_id)
    
    # Download the data file
    download_file_path <- file.path("/path/to/downloaded_data/rna_seq", paste0(data$file_name))
    download.file(download_url, destfile = download_file_path, mode = "wb")
    
    # Log clinical attributes (You might have to format this based on the data returned)
    clinical_attributes <- as.data.frame(data$cases)
    output_path <- "/path/to/output/clinical_attributes.csv"
    write.csv(clinical_attributes, file = output_path, row.names = FALSE, append = TRUE)

    print(paste("Downloaded:", download_file_path))
  }
}

# Run the download process for both projects
for (project_id in project_ids) {
  download_gdc_data(project_id)
}