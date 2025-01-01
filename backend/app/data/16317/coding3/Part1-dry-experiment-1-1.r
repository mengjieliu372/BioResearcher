# Load necessary libraries
library(httr)  # For API requests
library(jsonlite)  # For JSON handling
library(dplyr)  # For data manipulation

# Define the API Keys
TCGA_API_KEY <- "your_tcga_api_key"  # <-- Insert your TCGA API key
GTEx_API_KEY <- "your_gtex_api_key"  # <-- Insert your GTEx API key

# Function to query TCGA for liposarcoma samples
get_tcga_samples <- function() {
  url <- "https://api.gdc.cancer.gov/v0/cases"
  
  query_parameters <- list(
    filters = jsonlite::toJSON(list(
      op = "and",
      content = list(
        list(
          op = "in",
          content = list(
            field = "cases.disease_type",
            value = c("Liposarcoma")
          )
        )
      )
    )),
    fields = "case_id,sample_id,project.disease_type,submitter_id,collection_date",
    size = 100
  )
  
  response <- GET(url, query = query_parameters, add_headers(Authorization = paste("Bearer", TCGA_API_KEY)))
  
  content_type <- headers(response)$`content-type`
  if (!grepl("application/json", content_type)) {
    print(paste("TCGA response is not JSON. Status Code:", status_code(response)))
    print(content(response, "text"))
    stop("Failed to retrieve data from TCGA. Check API credentials or endpoint.")
  }

  samples <- content(response, as = "parsed", type = "application/json")
  liposarcoma_samples <- samples$data
  return(liposarcoma_samples)
}

# Function to query GTEx for sarcoma samples using GTEx V2 API
get_gtex_samples <- function() {
  url <- "https://gtexportal.org/api/v2/samples"  # Updated to v2 API
  
  response <- GET(url, add_headers(Authorization = paste("Bearer", GTEx_API_KEY)))
  
  content_type <- headers(response)$`content-type`
  if (!grepl("application/json", content_type)) {
    print(paste("GTEx response is not JSON. Status Code:", status_code(response)))
    print(content(response, "text"))
    stop("Failed to retrieve data from GTEx. Check API credentials or endpoint.")
  }
  
  samples <- content(response, as = "parsed", type = "application/json")
  
  # Extract relevant sample information for sarcoma
  sarcoma_samples <- samples$data %>%
    filter(sample_type == "sarcoma")

  return(sarcoma_samples)
}

# Function to simulate local biobank samples
get_local_biobank_samples <- function() {
  local_samples <- data.frame(
    sample_id = c("LB001", "LB002"),
    source = c("Local Biobank", "Local Biobank"),
    tissue_type = c("Frozen", "Paraffin"),
    collection_date = as.Date(c('2021-01-01', '2021-02-01'))
  )
  
  return(local_samples)
}

# Main Execution
tryCatch({
  tcga_samples <- get_tcga_samples()
  gtex_samples <- get_gtex_samples()
  local_samples <- get_local_biobank_samples()

  # Combine all samples
  all_samples <- bind_rows(tcga_samples, gtex_samples, local_samples)

  # Save combined samples to a CSV file
  write.csv(all_samples, file = "/path/to/output/combined_samples.csv", row.names = FALSE)
  print("Sample metadata has been saved to /path/to/output/combined_samples.csv")
}, error = function(e) {
  print(paste("An error occurred:", e$message))
})