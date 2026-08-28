# Shared Cleaned Data

This folder contains the cleaned dataset and KNIME workflow used for the group Business Intelligence analysis.

## Analysis Scope

The dataset focuses on US job postings requiring Business Analysis skills.

## Data Preparation Process

The KNIME workflow includes:

1. Importing the job postings and job skills datasets
2. Joining the datasets using `job_link`
3. Filtering records where `search_country = United States`
4. Filtering job postings containing the skill `Business Analysis`
5. Checking duplicate and missing values
6. Validating geographic information
7. Preparing the cleaned dataset for further group analysis

## Files

- `BA_Job_Market_Analysis_Workflow.knwf` – KNIME workflow used for data preparation
- `BA_related_US_jobs_2024_cleaned.csv` – cleaned dataset used for subsequent analysis

## Purpose

This cleaned dataset provides a consistent analytical base for all group members conducting further analysis.
