# Azure Serverless ETL Pipeline

### What's an ETL Pipeline ?
### ETL (Extract, Transform, Load): A data pipeline process where data is extracted from sources, transformed into the desired format and loaded into a storage system or database. 

## Project Overview

This project demonstrates a complete end-to-end serverless data pipeline on Azure for analyzing household energy consumption. It uses a series of Azure services and Python applications to ingest raw data, transform it, store it and serve it via an API for analytics and machine learning frontend.

### Goals of the project:
- Build a cost-efficient, scalable and event-driven pipeline.
- Automate data ingestion, transformation and storage with minimal infrastructure management.
- Leverage Azure Functions, Blob Storage and Cosmos DB for seamless serverless execution.

## ⚙️ Architecture  

### 1. Data Ingestion (Extract)
- Raw CSV data is uploaded into Azure Blob Storage.
- A Blob Trigger in the Azure Function App automatically starts the ETL pipeline whenever a new file is uploaded.

### 2. Transformation (Transform)
- The Azure Function processes and cleans the incoming data.
- This includes parsing, validation, and formatting to match the target schema.
- Additional enrichment and filtering, such as forecasting with the **Prophet** model or detecting anomalies with the **Isolation Forest** model, is applied to the data.

### 3. Data Loading (Load)
- The transformed data is loaded into Azure Cosmos DB for structured queries and analytics.
- The entire cloud infrastructure is defined and managed using **Terraform**, ensuring a repeatable and automated deployment process.

### 4. Application Layer
- A set of **HTTP Trigger APIs** expose endpoints for the frontend.
- These functions allow for retrieving aggregated data, running forecasts, and detecting anomalies.

### 5. Frontend
- A **Streamlit** web application provides an interactive user interface to visualize energy data, run analytics, and interact with the forecasting and anomaly detection APIs.

### 6. Monitoring & Logging
- Application Insights monitors the pipeline's performance and logs errors.
- The serverless architecture allows the entire solution to scale automatically with the workload, ensuring efficient resource utilization.