# Data Engineering Project

You are my data engineering mentor. Continue this project using the agreed requirements below. This document is the project specification, not a claim that implementation has already been completed.

## 1. Goal and working relationship

I am building a portfolio project to apply for junior data engineer roles. I need to understand every step and explain the architecture, code, trade-offs, failures, and recovery procedures in interviews. Prioritize a reliable, readable, reproducible project over unnecessary complexity.


### Mandatory teaching and execution instructions

1. Do not rush. Discuss the workload, architecture, tools, and configuration before implementation. The architecture below has already been agreed; do not restart the entire discussion unless there is a concrete problem.
2. Work one small step at a time. Explain the purpose of each step, provide only the commands or code needed for that step, wait for my output, verify it, and then continue. Do not give several implementation phases at once.
3. Explain imports, configuration, commands, SQL, and important code decisions in plain language. Define unfamiliar terms before using them. I want practical understanding, not unexplained copy-pasting.
4. The source selection and 14 weather + 8 air-quality fields are already approved. Before implementation, explain their units and relevant limitations as needed; do not ask for reapproval unless an actual incompatibility appears.
5. Do not run project code, install packages, retrieve datasets, or change my environment on your side. I will execute the supplied commands on my laptop and share results. Documentation research is allowed.
6. Preserve original source values during ingestion. Do not calculate daily summaries, convert units, fill missing values, remove duplicates, or perform feature engineering during raw retrieval. These transformations belong in the downstream pipeline.
7. Build respectful API clients: conservative request rates, timeouts, bounded retries, exponential backoff with jitter, Retry-After handling, caching/checkpoints, and resumable downloads. Respect source terms and attribution. Do not promise that blocking can be made impossible.
8. Do not ask repeatedly for decisions already settled here. Clearly distinguish agreed decisions from proposals still requiring discussion.
9. Do not mix Kafka and ML implementation into the main pipeline now. Their objective is defined here, but they are a later extension.
10. Keep communication and documentation professional and readable. Never claim a check passed, data was retrieved, or a component was completed without evidence from my results.



## 2. Environment and existing repository

- Originally specified environment: Linux Mint 22.3 "Zena", XFCE, bash shell, Visual Studio Code as editor.
- Hardware: 12 GB RAM, 1 TB HDD, Intel Core i7-7700HQ, Intel integrated GPU, NVIDIA GTX 1050 Mobile with 4 GB VRAM.
- Target Python: 3.12. However, Python in the Linux Mint XFCE system is 3.12.4. So, we need to create dedicated `.venv` using python3.12. That `.venv` must have packages so that we can freeze all required packages into `requirements.txt`.
- GitHub repository: `https://github.com/vasif-asadov1/weather_analysis_pipeline`
- Existing local folder: `/home/vasif/Projects/Weather Data Engineering`
- An SSH key is already configured. Check the local folder and remote repository state before initializing, cloning, or connecting them. Do not overwrite existing work or invent their current contents.
- Airflow and later Kafka will run locally through Docker when I start them. They are not expected to run continuously. Choose resource-conscious configurations and bring up only necessary services.
- Snowflake is selected for this project. I reported 25 trial days remaining during planning; that was a historical report, not a permanent remaining balance. Check the actual expiry when needed. Do not assume trial credits last beyond the calendar deadline.
- A future second project may use a fully free setup. Do not change this project's warehouse to MotherDuck, DuckDB, or PostgreSQL without discussion.


## 3. Geographic scope and TürkiyeAPI v2 — FINALIZED

- Analyze **all 81 provincial centers of Türkiye**, not 81 entire provinces or 25 international cities. The API request coordinates must represent the provincial centers; verify their semantics (city center vs centroid) before treating them as such.
- Use **TürkiyeAPI v2** geographic reference data, previously inspected at `https://api.turkiyeapi.dev/v2/datasets/provinces.json`. Previous user-run checks found **81 records, 81 unique province IDs/names, valid coordinates, and seven geographic regions**.
- Desired reference fields: stable `province_id` (TürkiyeAPI ID), province/city name, region name, population, elevation above sea level (rakım), province area, postal code, latitude, longitude, and country name (`Türkiye`). Keep IANA time zone (`Europe/Istanbul`) as project reference metadata.
- **Verify field availability and meaning against the actual response**. Population, elevation, area, and postal code are requested attributes, not yet confirmed to exist in the inspected endpoint. Do not invent absent attributes or silently substitute incompatible fields; document omissions or obtain a separately approved source. Population needs an as-of/reference year; area refers to a province, not its city center.
- Use the stable `province_id` as the location linkage key. Do not join using city names or floating-point coordinates. Build `GOLD.DIM_LOCATIONS` from the verified reference data; weather and air-quality fact records link by `province_id`.
- Keep both **requested city-center coordinates** (from TürkiyeAPI) and **returned model-grid coordinates** (from each Open-Meteo API). The two source grids can differ and multiple cities may map to one grid cell.
- Keep source API JSON unchanged and attach `province_id`, province name, country, requested coordinates, request parameters, retrieval timestamp, and provenance separately via file path or sidecar/manifest. Avoid modifying original measurement payloads merely to attach metadata.

## 4. Main architecture — agreed

The main project is historical ingestion, local raw storage, Snowflake medallion tables, dbt, Airflow, and Streamlit.

1. Retrieve original historical weather and air-quality files into local folders.
2. Preserve original files and source metadata.
3. Upload loadable files to Snowflake named internal stages.
4. Load source records into Snowflake Bronze.
5. Use dbt to build clean Silver records and analytical Gold tables, with tests.
6. Export validated Gold tables to local snapshots for recovery.
7. Connect Streamlit directly to Snowflake Gold, using Plotly charts.
8. Use Airflow to orchestrate weekly weather updates through this pipeline.

Local Gold exports are backups/snapshots. They are not the main dashboard data source while Snowflake is available. A same-disk copy does not protect against disk failure. Plan exports before trial expiry; changing the dashboard to a local backend afterward is a separate task.



## 5. Local storage and raw-data rules — FINALIZED FOR INITIAL BACKFILL

Use ordinary local folders, accessible from the host and later bind-mounted into Docker containers. Raw files must survive container removal and remain excluded from Git.

**Approved initial historical storage design: Option B — original, uncompressed `.json` files, organized by source → `province_id` → year.** The reference source is stored separately. No monthly partitioning is required for the initial archive. A full calendar year is the preferred retrieval/file unit, provided the request succeeds; a partial latest year can have a partial-year JSON response. Preserve actual API responses as received, not reconstructed or aggregated payloads.

```text
data/
├── raw/
│   ├── reference/
│   │   └── turkiyeapi/
│   │       └── provinces.json
│   ├── weather/
│   │   ├── province_id=1/
│   │   │   ├── 2015.json
│   │   │   └── 2016.json
│   │   └── province_id=81/
│   │       └── ...
│   └── air_quality/
│       ├── province_id=1/
│       │   ├── 2015.json
│       │   └── 2016.json
│       └── province_id=81/
│           └── ...
├── manifests/
├── load_ready/                 # only if needed; no automatic duplicate copies
├── exports/gold/
└── forecasting/                # deferred Kafka/ML branch
```

For 2015–2025 inclusive, **81 × 11 × 2 = 1,782 environmental annual files**, plus files for 2026 or later partial/full years. The number of files is manageable by code; never upload/manage files manually. One sample full-year Ankara response was 0.70 MB weather and 0.49 MB air quality, but these are **not** reliable universal size estimates.

- First priority: **one-time historical backfill** from 2015-01-01 to each source's latest available historical date. Do not mix this implementation with weekly update logic.
- Later: Airflow will retrieve **only the eligible recent week's hourly weather data**, not re-download the full archive. Design weekly file naming separately when implementing Airflow. Air-quality weekly updates are not part of the agreed initial Airflow DAG.
- Preserve source values and units; no ingestion-time imputation, zero-filling, daily summaries, deduplication, or analytical conversions. JSON `null` must remain missing, never be interpreted as zero.
- Use an ingestion manifest/checkpoint for source, province ID, year/date range, file path, requested/returned coordinates, retrieval time, success/error, timestamp count, checksum, and validation status. Do not overwrite successfully validated historical files accidentally. Retry only failed/missing periods; if an annual API request proves too large for another province/year, use a documented smaller fallback batch without claiming it is the same original annual response.
- Validate every response: HTTP/API errors, JSON parse, expected fields, timestamp range/count and uniqueness/continuity, consistent array lengths, and non-null counts. Allow legitimate missing pollutant values; do not mark a valid response failed merely because older variables are entirely null.
- Implement respectful rate limits, timeouts, bounded retries with backoff/jitter, `Retry-After` handling, and resumability. Check current Open-Meteo usage limits/licensing before full-scale backfill.

## 6. Historical weather source and feature scope — APPROVED AND SAMPLE-TESTED

- Source: **Open-Meteo Historical Weather API**, `https://archive-api.open-meteo.com/v1/archive`.
- Explicit model selection: `models=era5`; hourly data, `timezone=UTC`.
- Geographic scope: all 81 Turkish provincial-center coordinates supplied by the verified TürkiyeAPI reference.
- Start date: **2015-01-01**. End date: latest **actually available** historical ERA5 date, respecting its publication delay; do not assume today is available.
- Approved exact **14 hourly API fields** (do not reopen selection):

| # | Exact API field | Meaning |
| --- | --- | --- |
| 1 | `temperature_2m` | Air temperature at 2 m |
| 2 | `relative_humidity_2m` | Relative humidity at 2 m |
| 3 | `dew_point_2m` | Dew-point temperature at 2 m |
| 4 | `rain` | Rain amount over the provider's interval |
| 5 | `precipitation` | Total precipitation over the provider's interval |
| 6 | `snowfall` | Snowfall amount/depth as provided |
| 7 | `wind_speed_10m` | Wind speed at 10 m |
| 8 | `wind_direction_10m` | Wind direction at 10 m |
| 9 | `pressure_msl` | Mean sea-level pressure |
| 10 | `surface_pressure` | Surface pressure |
| 11 | `cloud_cover` | Cloud cover |
| 12 | `shortwave_radiation` | Shortwave solar radiation |
| 13 | `sunshine_duration` | Sunshine duration |
| 14 | `weather_code` | Weather condition code |

Use exact names **`surface_pressure`**, not `surface_pressure_level`, and **`weather_code`**, not `weather_codes`. Preserve the units reported in `hourly_units`; don't assume precipitation and rain are additive, or confuse snowfall units with rainfall units. No other weather fields are approved.

**User-executed proof of concept:** Annual request for Ankara (requested `39.9334, 32.8597`), 2015-01-01 through 2015-12-31, ERA5/UTC, succeeded. Returned **8,760 hourly timestamps**, first `2015-01-01T00:00`, last `2015-12-31T23:00`; **all 14 fields had 8,760/8,760 non-null values**, array lengths passed, JSON file size ~**0.70 MB**; returned model grid coordinates **40.0, 32.75**. This verifies one annual example, not all provinces/years.

## 7. Historical air quality — APPROVED AND SAMPLE-TESTED

**Final source selection replaces the previously proposed CAMS EAC4/Copernicus direct GRIB/NetCDF download:** use **Open-Meteo Air Quality API**, `https://air-quality-api.open-meteo.com/v1/air-quality`, explicitly `domains=cams_europe`, `timezone=UTC`. This serves CAMS European modeled/reanalysis air quality through a convenient API; it is **modeled gridded data, not physical measurements at each city center**. Document resolution, source limitations, usage terms, and potential mismatch with station measurements. No CAMS Europe bulk NetCDF downloads and no direct EAC4 integration in v1.

- Start date: **2015-01-01**; end date: latest **actually available historical** data for the selected model.
- Hourly source records; no daily aggregations during retrieval. Silver retains hourly weather **and hourly air quality**.
- Approved exact **8 API fields** (PM1 is **not** part of the approved set):

| Pollutant | Exact Open-Meteo API field |
| --- | --- |
| PM2.5 | `pm2_5` |
| PM10 | `pm10` |
| NO | `nitrogen_monoxide` |
| NO₂ | `nitrogen_dioxide` |
| NH₃ | `ammonia` |
| O₃ | `ozone` |
| SO₂ | `sulphur_dioxide` |
| CO | `carbon_monoxide` |

Preserve `hourly_units` (the user samples reported **µg/m³** for all eight), all timestamps, original values and `null`s. Do not synthesize missing historic pollutant measurements, convert null to zero, or treat absence as zero pollution. Do not invent AQI by averaging concentrations.

**User-executed Ankara sample tests**, all with 48/48 timestamps per two-day period:

| Sample period | Non-null fields | Entirely null fields |
| --- | --- | --- |
| Jan 15–16, 2015 | PM2.5, PM10, NO₂, O₃ | NO, NH₃, SO₂, CO |
| Jan 15–16, 2016 | PM2.5, PM10, NO₂, O₃, SO₂, CO | NO, NH₃ |
| May 15–16, 2016 | PM2.5, PM10, NO₂, O₃, SO₂, CO | NO, NH₃ |
| Jan 15–16, 2018 | All eight | None |
| Jan 15–16, 2022 | All eight | None |

**Full-year Ankara 2015 proof of concept:** 8,760 hourly timestamps (2015-01-01T00:00 through 2015-12-31T23:00), all eight arrays present with matching lengths, PM2.5/PM10/NO₂/O₃ each **8,760/8,760 non-null** and NO/NH₃/SO₂/CO each **0/8,760 non-null**; JSON size ~**0.49 MB**, returned model grid coordinates **39.9, 32.9**. Both weather and AQ annual requests succeeded.

These observations **do not establish whole-year coverage for 2016, 2018 or 2022, exact variable introduction dates, or complete coverage across 81 centers**. Do not hardcode missingness by calendar year: store actual API values and validate non-null coverage. 2015 remains the approved common ingestion start date despite missing fields. Missingness and completeness will be handled transparently in dbt.

Air quality is part of the initial historical backfill. **Weekly Airflow updates apply to weather only** in v1.

## 8. Snowflake organization and file loading — AGREED APPROACH

Proposed database: `WEATHER_ANALYTICS`, with schemas:

| Schema | Purpose |
| --- | --- |
| `INGESTION` | Named internal stages and loading objects |
| `BRONZE` | Original source JSON as `VARIANT` plus ingestion metadata |
| `SILVER` | Validated, typed hourly weather and hourly air-quality records |
| `GOLD` | Daily summaries, `DIM_LOCATIONS`, other dimensions/facts, dashboard marts |

- **Local files cannot be loaded by Snowflake directly.** A Python-based bulk loader will use Snowflake's supported **`PUT`** operation to upload local JSON files into named **internal stages**; use **`COPY INTO`** in batches to load Bronze. No manual per-file upload or one-table-per-file scheme.
- Planned stages: `STG_REFERENCE`, `STG_WEATHER`, `STG_AIR_QUALITY`, with three corresponding source Bronze tables (exact table names to choose during implementation).
- Bronze should preserve original JSON in `VARIANT`, with source file/path and load metadata. Annual Open-Meteo JSON documents are one candidate Bronze row each, **subject to actual Snowflake `VARIANT`/file-size limits**; validate these before assuming every document fits. If not, use a value-preserving load-ready representation while retaining original JSON.
- `province_id` is not part of the Open-Meteo original payload. Preserve it in the staged path (e.g. `weather/province_id=6/2015.json`) or explicit manifest and derive it safely during Bronze load. Do not join on coordinates.
- Stage/upload files in controlled batches, use batched `COPY INTO`, reconcile source file counts against loaded counts, and implement safe reruns/idempotency. Snowflake load history is useful but not an unlimited guarantee against duplicate loads.
- Teach database vs schema vs table vs stage vs warehouse during setup. Use conservative compute settings, auto-suspend/resume, permissions, cost monitoring, and keep credentials out of Git. Do not enable paid services or add payment methods without approval.

## 9. dbt responsibilities

dbt transforms and tests data. Airflow is the overall workflow orchestrator.

### Silver

- Standardize column names, types, units, and timestamps.
- Join verified city identifiers and geographic metadata.
- Handle duplicates deterministically using documented keys and provenance.
- Validate missing values, ranges, and completeness; retain auditability of rejected/flagged records.
- Keep the useful source time resolution: **hourly weather and hourly air quality**.
- Explicitly choose UTC storage and a daily aggregation boundary. Discuss UTC versus city-local calendar days before daily models are finalized.

### Gold

- Build daily weather and pollution summaries.
- Choose correct aggregation by measurement: sums for interval precipitation, means/min/max as appropriate, and suitable circular/vector handling for wind direction.
- Do not sum instantaneous values or average direction angles naively.
- Define minimum coverage rules so partial days are not misrepresented as complete.
- Add useful calendar and analytical features after discussing them.
- Build a clear star schema, likely city/date dimensions and separate weather/pollution facts. Define grain and keys before SQL implementation.
- Avoid unsupported country-wide climate claims and distinguish partial current years from complete years.

### Tests and documentation

- Not-null, uniqueness, accepted-value, relationship, range, and completeness checks where meaningful.
- Incremental processing, safe reruns, and documented treatment of late/revised data.
- Explain `profiles.yml`, project configuration, sources, staging models, refs, materializations, tests, and lineage step by step.
- Keep credentials out of Git; use environment variables or local secret configuration.
- Generate dbt documentation and publish a sanitized static documentation site with a link in README.md. Review compiled SQL, metadata, and artifacts before publication.
- dbt tests alone do not make publication atomic. Design a proportionate validation/publication approach so failed checks do not expose invalid new dashboard results; explain this before claiming that guarantee.



## 10. Airflow weekly DAG

I am new to Airflow. Teach DAGs, tasks, dependencies, scheduling, data intervals, logical dates, catchup, retries, and task logs before expecting me to use them.

Intended schedule: Wednesday 00:00. Europe/Istanbul was proposed but must be explicitly confirmed before configuration. Use an explicit timetable/catchup setup appropriate to the pinned Airflow version; do not assume defaults.

The weekly DAG orchestrates **only the recent eligible week of weather data**, not a repeat of the initial historical backfill:

1. Determine the most recent eligible **one-week** weather interval using ERA5 availability and checkpoints (and recover genuinely missed weekly intervals if needed).
2. Retrieve only that eligible week of hourly weather into local raw folders; do not re-download 2015-to-present history.
3. Upload successful batches to Snowflake internal stage.
4. Load Bronze safely.
5. Execute dbt transformations and quality checks with sensible dependency order.
6. Publish validated analytical outputs using the agreed mechanism.
7. Export Gold snapshots locally and record run status.

The final export format, retention, and full-versus-incremental snapshot policy remain to be agreed.

Operational requirements:

- The laptop is not always running. Airflow performs no work while its services are stopped.
- On restart, recover eligible missed completed intervals. Record actual execution time honestly; never pretend execution happened on Monday.
- Rerunning an interval must not create duplicate logical records.
- Distinguish safe raw append-only history from deduplicated current analytical records.
- Use bounded retries, checkpoints, persistent Airflow metadata, clear logs, and controlled backfill concurrency.
- Do not pass large datasets through XCom; pass file paths/batch references.
- Demonstrate a successful run, a retry/recovery, a safe rerun, and missed-period recovery.
- Document setup and operation in README.md.


## 11. Main Streamlit dashboard

- Use Streamlit with Plotly, querying Snowflake Gold directly.
- Include city comparisons, temperature changes over years/seasons, rainfall/wind analysis, and pollution analysis as supported by agreed Gold models.
- Define cache expiration and query-refresh behavior. An open dashboard does not redraw solely because a warehouse table changed.
- Show latest successful pipeline time, latest available dates, and completeness where relevant.
- Keep credentials secure and queries efficient to reduce Snowflake compute use.
- Local Gold snapshots are recovery copies; local fallback after trial expiry is optional future work.
- Streamlit runs separately from the weekly DAG. Airflow does not need to start it during every weekly update.
- A later navigation link/page will lead to hourly weather and forecasting.


## 12. Later extension: Kafka and ML

Objective is agreed; implementation is deferred until the main pipeline and dashboard work.

### Independent dataset

- Copy the initially collected hourly weather history into a separate forecasting folder.
- New Kafka-fed records extend this separate dataset, not the main historical weather files or the Snowflake weekly branch.
- Use historical seed files plus incoming batches if more reliable than editing one huge CSV. They form one logical dataset.

### Event workflow

1. A Python producer polls a weather API hourly while running.
2. It publishes hourly weather records to Kafka.
3. A consumer validates and persists records locally.
4. Prediction jobs run after successful persistence.
5. Streamlit displays saved hourly records and predictions through a separate page/link.

Use the same relevant measurement groups as historical weather, with explicitly supported extras if approved. Preserve event/valid time, retrieval time, city_id, source model, record type, and event identifiers. Handle overlaps, duplicates, out-of-order records, and replay. Current modeled conditions and future forecasts must be distinguished.

The historical ERA5 seed and recent weather model output may differ. Do not silently treat them as identical data distributions or feed future forecast rows into an observations table.

### ML scope to decide later

- Define a concrete target and forecast horizon before choosing an algorithm.
- Start with a baseline, then compare models using chronological evaluation and leakage-safe features.
- Decide whether historical hourly features need their own clean local processing path; do not train blindly on untouched raw values.
- Prediction automation and model retraining are separate decisions; do not retrain from scratch every hour by default.
- Train/predict outside Streamlit. Streamlit reads saved results.
- Bad-weather indicators or email notifications are optional, unimplemented ideas. Do not configure messaging without explicit agreement.
- Demonstrate Kafka producer/consumer behavior, offsets, replay, and persistence honestly. No claim of continuous operation when my laptop is off.


## 13. Repository, CI, and presentation

Propose a clean structure before creating it. Expected areas include:

- `src/`: ingestion, validation, loading, exporting, shared utilities.
- `dbt/`: the complete dbt project.
- `airflow/`: DAGs and relevant configuration.
- `app/`: Streamlit application.
- `notebooks/`: later EDA/ML experiments.
- `tests/`: meaningful checks.
- `config/`: non-secret configuration and city reference.
- `docs/`: architecture, data dictionary, operational instructions, decisions.
- Local ignored data directories for raw files, exports, and later forecasting.
- Docker/Compose configuration, dependency files, `.gitignore`, `.env.example`, `README.md`.
- `.github/workflows/`: CI (note the leading dot).

Do not commit secrets, local profiles containing passwords, large datasets, generated logs, or virtual environments. Keep safe example configuration.

Start CI with linting, focused tests, and appropriate dbt/configuration validation. Do not require expensive live cloud jobs on every commit. GitHub Actions is not currently selected to host a permanent Airflow service. Scheduled cloud execution can be discussed later; running an ephemeral Docker Airflow stack in Actions is not required.

README must explain the problem, architecture, source limitations/licences, setup, data grain, tests, DAG behavior, reruns/catchup, costs/trial limitations, screenshots, published dbt documentation link, and what actually runs locally versus in Snowflake. Show observed results, not invented performance figures.


## 14. Implementation sequence and verification gates — UPDATED

| Phase | Work | Evidence before moving on |
| --- | --- | --- |
| 1 | Inspect actual local repository/environment and current Snowflake trial status; create/activate Python 3.12 `.venv` and minimal project scaffolding | User command output confirms environment and files; no overwrite |
| 2 | Implement TürkiyeAPI v2 reference retrieval, verify 81 IDs/coordinates and available reference attributes, save original `provinces.json` | User-run JSON validation and field inventory |
| 3 | Implement validated, resumable annual ERA5 weather JSON retrieval for 81 centers, from 2015 through latest available history | User-run sample then backfill coverage/integrity report |
| 4 | Implement validated, resumable annual CAMS Europe air-quality JSON retrieval, preserving missing values | User-run sample then backfill coverage/integrity report |
| 5 | Configure Snowflake stages and Bronze bulk `PUT`/`COPY INTO` loads | Sample load, full file reconciliation, metadata correctness |
| 6 | Build dbt Silver/Gold, daily completeness rules, `DIM_LOCATIONS`, tests and documentation | Verified models, grain, null handling, tests |
| 7 | Implement Airflow **one-week weather-only** ingestion and downstream pipeline | Successful run, retry, safe rerun, missed interval recovery |
| 8 | Build Streamlit/Plotly dashboard and Gold local exports | Correct charts and verified data refresh |
| 9 | Finish CI, README, documentation, demonstration | Reproducible main project |
| 10 | Implement separate Kafka + ML extension | Independently defined and verified later |

The source choices, 22 environmental fields, 2015 start date, annual JSON raw archive, and initial Snowflake upload approach are **already agreed**. Do not reopen them without a concrete failure. Keep the main project achievable within the actual remaining Snowflake trial period.

## 15. Verified current state and exact first response for the new chat

**Already decided and verified by the user:**
- TürkiyeAPI v2 reference endpoint was inspected: 81 unique province IDs/names, seven regions, valid coordinates. Additional desired fields (population, elevation, area, postal code) are **not yet confirmed**.
- Open-Meteo weather: all 14 approved ERA5 fields returned 8,760 non-null hourly values in the Ankara **full-year 2015** test; JSON ~0.70 MB; timestamp and array-length checks passed.
- Open-Meteo air quality: all eight approved CAMS Europe fields were returned in Ankara **full-year 2015** test with 8,760 timestamps and matching lengths; four fields all null in that year; JSON ~0.49 MB. Two-day 2016, 2018 and 2022 checks are described above.
- The **initial backfill** will use one annual source JSON per province/source/year wherever API response size and limits permit, organized in source/province/year folders. Weekly updates are a **later** weather-only Airflow phase.
- Snowflake named internal stages, bulk `PUT`, batch `COPY INTO`, Bronze `VARIANT`, dbt Silver/Gold, Streamlit and local Gold backups are agreed architecture, **not yet implemented or tested**.
- User ran the API tests manually using terminal `curl` and Python standard library, saving temporary samples under `/tmp`. These sample files are **not evidence that the project repository, ingestion code, Python 3.12 environment, Snowflake objects, or complete historical archives already exist**.

**Your first response in the new chat:** Briefly acknowledge the approved plan. **Start implementation Phase 1 only:** ask the user to run a minimal set of safe, read-only commands to inspect the existing repository path, Git remote, installed Python versions and available virtual environments, then wait for their output. Do not provide the whole codebase or multiple implementation phases at once. Do not repeat the source/field debate. Once environment is confirmed, implement TürkiyeAPI reference retrieval as the first coding task. The user runs every command and shares results; you do not run project code or install anything on your side.
