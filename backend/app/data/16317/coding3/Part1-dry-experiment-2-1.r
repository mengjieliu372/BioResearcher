# Load required libraries
if (!requireNamespace("httr", quietly = TRUE)) {
    install.packages("httr") # You can uncomment this line to install if necessary
}
if (!requireNamespace("jsonlite", quietly = TRUE)) {
    install.packages("jsonlite") # You can uncomment this line to install if necessary
}

library(httr) 
library(jsonlite)

# Check connectivity to a known public API
test_url <- "https://jsonplaceholder.typicode.com/posts"
response <- GET(test_url)

# Check if the request was successful and print the result
if (response$status_code == 200) {
    print("Successfully connected to the public API. Here are the first few entries:")
    print(head(fromJSON(content(response, "text"))))
} else {
    print(paste("Error connecting to the public API. Status code:", response$status_code))
}