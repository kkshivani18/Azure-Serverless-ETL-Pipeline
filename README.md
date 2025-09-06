# Azure Serverless ETL Pipeline

### What's an ETL Pipeline ?
### ETL (Extract, Transform, Load): A data pipeline process where data is extracted from sources, transformed into the desired format and loaded into a storage system or database. 

## Project Overview

This project implements a serverless ETL (Extract, Transform, Load) pipeline on Microsoft Azure. The pipeline ingests raw data from various sources, processes and transforms it using serverless compute and loads the curated data into a destination for analytics and reporting.

### Goals of the project:
- Build a cost-efficient, scalable, and event-driven pipeline.
- Automate data ingestion, transformation and storage with minimal infrastructure management.
- Leverage Azure Functions, Blob Storage and Cosmos DB for seamless serverless execution.

## ⚙️ Architecture

### 1. Data Ingestion (Extract)
- Source data is uploaded into Azure Blob Storage (Data lake - raw/landing container).
- Events in Blob Storage trigger the ETL pipeline automatically.

### 2. Transformation (Transform)
- Azure Functions process and clean the incoming data.
- Data transformations include parsing, validation and formatting to match target schema.
- Additional enrichment or filtering is applied before storing.

### 3. Data Loading (Load)
- Transformed data is loaded into Azure Cosmos DB for structured queries and analytics.
- Processed data can also be exported back into Blob Storage (processed container) for archival or reporting.

### 4. Monitoring & Logging
- Application Insights monitors pipeline performance and logs errors.
- Scales automatically with workload due to serverless architecture.

