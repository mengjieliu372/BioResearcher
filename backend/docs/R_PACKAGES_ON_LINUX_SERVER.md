# R Packages Setup on Linux Server (rocker/verse)

This project currently executes R code in Docker image `rocker/verse` (configured in backend code).

Use this guide on your Linux server to install required R/Bioconductor packages into a local image, while keeping executor config unchanged.

## 1) Prerequisites

- Docker installed and running
- Network access to:
  - `docker.io` (for image pull)
  - CRAN / Bioconductor mirrors (for package install)

## 2) Pull base image

```bash
docker pull rocker/verse:latest
```

## 3) Backup current local image (recommended)

```bash
TS=$(date +%Y%m%d-%H%M%S)
docker tag rocker/verse:latest bioresearcher/rocker-verse-backup:$TS
```

## 4) Start a temporary container

```bash
docker create --name br-verse-bootstrap rocker/verse:latest tail -f /dev/null
docker start br-verse-bootstrap
```

## 5) Install packages inside container

```bash
docker exec br-verse-bootstrap R -q -e "install.packages(c('BiocManager','jsonlite','data.table','readxl','httr','curl'), repos='https://cloud.r-project.org')"
docker exec br-verse-bootstrap R -q -e "if(!requireNamespace('BiocManager', quietly=TRUE)) install.packages('BiocManager', repos='https://cloud.r-project.org'); BiocManager::install(c('DESeq2','limma','edgeR','GEOquery','affy','gcrma'), ask=FALSE, update=FALSE)"
```

## 6) Commit patched image and overwrite local rocker/verse tag

```bash
docker commit br-verse-bootstrap bioresearcher/rocker-verse-with-pkgs:latest
docker tag bioresearcher/rocker-verse-with-pkgs:latest rocker/verse:latest
```

## 7) Verify required packages

```bash
docker run --rm rocker/verse:latest R -q -e "pkgs<-c('DESeq2','limma','edgeR','GEOquery','affy','gcrma','jsonlite','readxl'); cat(paste(pkgs, sapply(pkgs, requireNamespace, quietly=TRUE), sep='='), sep='\n')"
```

Expected: all packages print `=TRUE`.

## 8) Cleanup temporary container

```bash
docker rm -f br-verse-bootstrap
```

## 9) Rollback (if needed)

List backup tags:

```bash
docker images | grep bioresearcher/rocker-verse-backup
```

Rollback example:

```bash
docker tag bioresearcher/rocker-verse-backup:YYYYMMDD-HHMMSS rocker/verse:latest
```

## 10) Start backend

After package verification passes, start backend as usual.
No code change is needed because backend still uses `image="rocker/verse"`.

