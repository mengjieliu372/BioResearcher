# Preprocessing Steps Documentation (Part 2 - Dry Experiment 4)

## Overview
This document summarizes all preprocessing steps performed in Part 2 of the dry experiment.
The goal is to ensure reproducibility of data preparation, quality control (QC), and normalization.
All steps were designed to be robust to missing files by issuing warnings and using placeholders.

## Input Files (Allowlisted Sources)
The following files were designated as inputs for preprocessing and documentation:

| File | Exists |
|---|---|
| /workspace/data/GSE202361_AllSamples_rawcount.txt.gz | Yes |
| /workspace/data/GSE168205_annotated_combined.counts.txt.gz | Yes |
| /workspace/data/GSE230773_Read_counts.xlsx | Yes |
| /workspace/data/GSE202361_AllSamples_TPM.txt.gz | Yes |
| /workspace/data/GSE247026_Sample_genes_fpkm.xlsx | Yes |
| /workspace/data/GSE55465_non-normalized_INT-B.txt.gz | Yes |
| /workspace/data/GSE213065_Sarcoma_ecotyper_tpm_bulksamples.txt.gz | Yes |
| /workspace/data/GSE91061_BMS038109Sample.hg19KnownGene.rld.csv.gz | Yes |

## Step 1: Data Staging / Acquisition
**Objective:** Collect and stage available RNA-seq or expression matrices from local GEO files.

**Procedure:**
- Check presence of each allowlisted input file using `file.exists()`.
- For missing files: log a warning and create placeholder entries in manifests or outputs.
- Store staged files under `/workspace/coding3/part2_downloads/`.
- Generate download manifest and log:
  - `/workspace/coding3/part2_download_manifest.csv`
  - `/workspace/coding3/part2_download_log.txt`

**Rationale:** Ensure all expected datasets are accounted for, even if unavailable, to preserve reproducibility.

## Step 2: Quality Control (QC)
**Objective:** Evaluate sample quality and detect outliers or low-quality samples.

**Procedure:**
- Compute standard QC metrics (library size summaries, missingness, dispersion proxies).
- Generate QC outputs for traceability and visualization.
- Record sample provenance in a combined metadata table.

**Expected Outputs:**
- `/workspace/coding3/qc_report.txt`
- `/workspace/coding3/qc_metrics.csv`
- `/workspace/coding3/qc_excluded_samples.csv`
- `/workspace/coding3/rna_degradation_plot.png`
- `/workspace/coding3/qc_sample_sources_combined.csv`

**Rationale:** QC ensures downstream normalization and modeling are not biased by artifacts or poor-quality samples.

## Step 3: Normalization
**Objective:** Produce normalized expression matrices suitable for downstream differential analysis.

**Tools and Methods:**
- **DESeq2**: For count-based normalization using size factors and variance stabilization when applicable.
- **gcRMA / affy**: For microarray-style preprocessing when raw CEL or probe-level data are applicable.

**Typical Parameters (defaults unless specified):**
- `DESeqDataSetFromMatrix()` with count data and design matrix.
- `estimateSizeFactors()` and `counts(dds, normalized=TRUE)`.
- Optional filtering of low-count genes (e.g., keep genes with counts > 10 in ≥2 samples).
- gcRMA: background correction and quantile normalization via default `gcrma()` settings.

**Expected Output (example):**
- `/workspace/coding3/normalized_rna_counts.csv`

**Rationale:** Normalization removes library-size and technical biases to allow valid comparisons.

## Step 4: Documentation & Reproducibility Standards
**Core Practices:**
- No hard stops on missing files; create placeholders instead.
- Save all outputs under `/workspace/coding3/` with consistent naming.
- Record package versions and session info (below).

## Software and Package Versions
Key packages used (as available in environment):
- DESeq2
- limma
- edgeR
- GEOquery
- affy
- gcrma
- jsonlite
- readxl
- data.table
- httr
- curl

### R Session Info
```
R version 4.5.3 (2026-03-11)
Platform: x86_64-pc-linux-gnu
Running under: Ubuntu 24.04.4 LTS

Matrix products: default
BLAS:   /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3 
LAPACK: /usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.26.so;  LAPACK version 3.12.0

locale:
 [1] LC_CTYPE=en_US.UTF-8       LC_NUMERIC=C              
 [3] LC_TIME=en_US.UTF-8        LC_COLLATE=en_US.UTF-8    
 [5] LC_MONETARY=en_US.UTF-8    LC_MESSAGES=en_US.UTF-8   
 [7] LC_PAPER=en_US.UTF-8       LC_NAME=C                 
 [9] LC_ADDRESS=C               LC_TELEPHONE=C            
[11] LC_MEASUREMENT=en_US.UTF-8 LC_IDENTIFICATION=C       

time zone: Etc/UTC
tzcode source: system (glibc)

attached base packages:
[1] stats     graphics  grDevices utils     datasets  methods   base     

loaded via a namespace (and not attached):
[1] compiler_4.5.3
```

## Notes on Missing Data
If any allowlisted inputs are missing, documentation and manifests should contain placeholders.
This preserves reproducibility and audit trails, even when data are incomplete.

## Output Format
This documentation is saved as a Markdown file:
- `/workspace/coding3/preprocessing_steps_documentation.md`

End of document.
