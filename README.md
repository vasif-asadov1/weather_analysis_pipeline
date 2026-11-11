# Türkiye Weather & Air Quality Data Engineering Pipeline

An end-to-end data engineering portfolio project analyzing historical
weather and air quality across all 81 provincial centers of Türkiye.

## Project Objectives

- Collect historical hourly weather and air-quality data from 2015 onward.
- Preserve original API responses in a local JSON archive.
- Build a Bronze, Silver, and Gold data warehouse in Snowflake.
- Transform and validate datasets using dbt.
- Automate weekly weather updates using Apache Airflow.
- Develop an interactive analytical dashboard with Streamlit and Plotly.
- Demonstrate reliable ingestion, data quality, reproducibility, and recovery.

## Data Sources

| Source | Purpose |
|--------|---------|
| TürkiyeAPI v2 | Provincial reference data and coordinates |
| Open-Meteo ERA5 | Historical hourly weather (14 variables) |
| Open-Meteo CAMS Europe | Historical hourly air quality (8 variables) |

Historical data collection begins on January 1, 2015.

## Technology Stack

- Python 3.12
- Snowflake
- dbt
- Apache Airflow
- Docker
- Streamlit
- Plotly
- Git and GitHub

## Pipeline Architecture

TürkiyeAPI / Open-Meteo
        |
        v
Python Ingestion
        |
        v
Local Raw JSON Archive
        |
        v
Snowflake Internal Stages
        |
        v
Snowflake Bronze
        |
        v
dbt Silver / Gold
        |
        v
Streamlit Dashboard

Apache Airflow will orchestrate weekly weather updates and downstream
processing after the initial historical backfill is complete.

## Future Extension

A separate Apache Kafka and machine learning pipeline is planned for
hourly weather ingestion and forecasting.

This extension will not modify the main historical archive.

## Development Status

Project initialization in progress.

The repository structure and development environment are being prepared.
The production pipeline has not yet been implemented.

## Documentation

Architecture decisions, setup instructions, data dictionaries,
testing procedures, and recovery workflows will be added under `docs/`.

## License

No software license has been selected yet.
Data-source licensing and attribution requirements will be documented.
