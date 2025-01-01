# Load necessary libraries
library(knitr)
library(rmarkdown)

# Prepare the documentation content
doc_content <- '
# Preprocessing Documentation for RNA Sequencing Data

## Introduction
This document outlines the preprocessing steps taken in the analysis of RNA sequencing data, focusing on normalization methods applied in various datasets related to liposarcoma.

## Methods
1. **Quality Control** 
   - Software: FastQC
   - Description: Assess the integrity and quality of RNA samples.
   
2. **Normalization Methods**
   - **DESeq2**
     - Description: A method to normalize count data based on a model of the datasets.
     - Rationale: It accounts for differences in sequencing depth and RNA composition.
   - **gcrma**
     - Description: A method for normalizing Affymetrix GeneChip data.
     - Rationale: It uses a background adjustment based on probe-level data.

## Steps Taken
- **Load Data**: Used appropriate functions to load the RNAseq data from local files.
- **Quality Control Evaluation**: Conducted quality control checks and produced metrics visualizing sample quality.
- **Normalization**:
  - DESeq2 normalization used parameters:
    - `betaPrior = TRUE`
    - Size factors calculated based on the geometric mean of counts across samples.
  - gcrma normalization applied settings based on log2 transformations of expression data.

## Parameters
- **Input File Paths**:
  - `/path/to/downloaded_data/rna_seq/GSE202361_expression.txt`
  - `/path/to/downloaded_data/rna_seq/GSE205492_expression.txt`
  - etc.
- **Expected Outputs**: 
  - Normalized expression data saved in .txt files.
  - Quality control reports saved in specified directories.

## Conclusion
This documentation serves as a comprehensive reference for all preprocessing steps taken, ensuring reproducibility in future analyses.

'

# Define save path
output_path <- "/path/to/output/preprocessing_documentation.md"

# Write content to the markdown file
writeLines(doc_content, output_path)

# Print confirmation of successful documentation
print(paste("Documentation successfully saved to:", output_path))