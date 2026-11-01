StockGuard – Inventory Shrinkage Detection System

**YottaFlex AI Candidate Project**

StockGuard is an inventory shrinkage detection system designed to identify unusual stock losses by comparing calculated expected inventory with physical cycle-count quantities. It combines inventory movement processing, rule-based shortage detection, machine-learning anomaly detection, alert management, and investigation workflows.

> **Project status:** Core application workflows have been implemented and manually verified during development. Some technical and evaluation limitations are documented below. This is a local demonstration project, not a production-hardened inventory platform.

## 1. Business Problem

Retail businesses record inventory changes through receipts, sales, transfers, damage and other adjustments. Differences between expected stock and physical counts can indicate shrinkage or operational discrepancies.

StockGuard aims to:
- Calculate expected stock for a store and SKU.
- Compare expected stock with the latest physical cycle count.
- Identify potential shortages and surface them as alerts.
- Support investigation of detected alerts.
- Provide dashboard and model-performance views.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| ORM / database access | SQLAlchemy |
| Database | MySQL |
| Database migrations | Alembic |
| Anomaly detection | scikit-learn Isolation Forest |
| Data processing | Python, Pandas |
| API testing | Postman / HTTP requests |

Use the dependency files in the repository as the source of truth for exact versions.

## 3. Dataset

The development database was populated with the following synthetic dataset:

| Entity | Records |
|---|---:|
| Stores | 100 |
| SKUs | 5,000 |
| Inventory movements | 1,000,000 |
| Cycle counts | 20,000 |

The audited database also recorded 1,994 shrinkage-labelled cycle counts in the generated ground-truth data. These are synthetic labels and should not be interpreted as real-world shrinkage prevalence.

The audited dataset includes opening balances, sales, receipts, damage, transfers out and transfers in. The audit did not find populated adjustment or return movement rows. Do not assume those scenarios have been validated with populated data.

**Important:** Preserve the existing generated dataset. Do not run data-generation or reset commands against the populated database unless you have backed it up and explicitly intend to replace it.

## 4. Main Features

The application includes these user-facing areas:

- **Dashboard:** Summary view of shrinkage and alert information.
- **Stores:** Store listing.
- **Products / SKUs:** SKU catalog and search.
- **Inventory Lookup:** Look up expected stock and latest cycle-count information using a Store ID and SKU ID.
- **Shrinkage Alerts:** View and search shrinkage alerts.
- **Investigations:** Review and update investigation findings, resolution and status.
- **Model Performance:** View detection-model performance information.
- **System Health:** View application health information.

The inventory lookup API was manually verified using Store ID `11` and SKU ID `201`. It returned HTTP 200 with the store code, SKU code, expected stock and latest cycle count. The frontend lookup was subsequently tested successfully.

The investigation save/update workflow and alert-search focus behaviour were also manually tested after fixes.

## 5. Inventory and Detection Concepts

### Expected stock and variance

The system calculates expected inventory from recorded inventory movements and compares it with a physical cycle count.

Conceptually:

```text
Expected Stock = Opening Stock + Stock Increases - Stock Decreases

Variance = Counted Quantity - Expected Stock
```

The exact movement sign rules are implemented in backend services. The project audit identified duplicated movement-sign logic and noted that adjustment handling and historical `as_of` calculations need further consistency work.

Do not treat the simplified equation above as proof that every movement type or historical scenario is fully supported.

### Rule-based detection

The audited detection implementation includes a shortage threshold rule. The audit recorded a shortage threshold of 5 units. Its suitability depends on business context, SKU value, expected volume and operational policy.

### Isolation Forest

The project includes an Isolation Forest anomaly-detection approach. The project audit identified an evaluation limitation: the model was fitted and scored on the same rows rather than on a separate hold-out set. It also noted that synthetic labels were generated using shortage-related quantities that overlap with model features. Consequently, reported performance can be optimistic and must not be presented as evidence of real-world predictive accuracy.

A proper independent evaluation should use a separate hold-out dataset and document the split, features, label-generation process and limitations.

## 6. Application Architecture

```text
                  React + Vite Frontend
                           |
                           | HTTP / JSON
                           v
                     FastAPI Backend
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
       Inventory       Alerts &     Detection / ML
       Services      Investigations   Services
             |             |             |
             +-------------+-------------+
                           |
                           v
                      MySQL Database
                           |
                    SQLAlchemy ORM
                           |
                    Alembic Migrations
```

The frontend communicates with the FastAPI backend over HTTP. The backend uses SQLAlchemy to access MySQL, while Alembic manages database schema migrations.

## 7. Running the Project Locally

The commands below are a general local-development outline. Check the actual repository files and environment variables before running them.

### Prerequisites

- Python version compatible with `backend/requirements.txt`
- Node.js and npm compatible with the frontend project
- MySQL server
- Git

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the database connection using the environment variables expected by the backend. Do not commit your real `.env` file.

Start the API using the entry point configured in the project. For the usual FastAPI layout, this may be:

```bash
uvicorn app.main:app --reload
```

If the project is configured differently, follow its actual entry point.

### Frontend

In a separate terminal:

```bash
cd frontend
npm install
```

If the application uses a frontend environment file, configure its API base URL:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Build and lint checks:

```bash
npm run lint
npm run build
```

## 8. API Verification

The following inventory lookup endpoint was verified against the running local backend:

```http
GET /inventory/lookup?store_id=11&sku_id=201
```

Example response shape:

```json
{
  "store_id": 11,
  "store_code": "STORE-000001",
  "sku_id": 201,
  "sku_code": "SKU-000001",
  "expected_stock": "115.000",
  "latest_cycle_count": {
    "id": 1182,
    "count_code": "CNT-2026-000182",
    "counted_quantity": "108.000",
    "counted_at": "2026-03-29T18:13:00"
  }
}
```

This is a recorded local-development example, not a guarantee that the same values will exist in another database.

When enabled, FastAPI's interactive API documentation is normally available at:

```text
http://127.0.0.1:8000/docs
```

Use the running API's OpenAPI page as the authoritative list of routes and request schemas.

## 9. Verification Performed

The following checks were recorded during development:

- Frontend ESLint completed with no errors and one React Hook dependency warning.
- Vite production build completed successfully.
- Store and SKU listing endpoints returned populated records.
- Inventory lookup returned HTTP 200 for Store ID 11 and SKU ID 201.
- Frontend Inventory Lookup was tested successfully with those IDs.
- Investigation save/update and Shrinkage Alerts search-focus issues were fixed and manually verified.

These are development checks, not a claim that the application has a complete automated test suite.

## 10. Known Limitations and Further Work

The project audit identified the following areas for further improvement. Re-check the current source before treating each item as still outstanding, because development continued after the audit.

1. Unify movement-sign rules across inventory calculation, detection and data generation.
2. Add consistent historical expected-stock calculation using an `as_of` or cycle-count timestamp where required.
3. Validate adjustment and return movement handling with populated test data.
4. Add duplicate-alert protection and robust alert identifiers.
5. Add duplicate-investigation protection and synchronize alert status when an investigation is resolved or closed.
6. Add pagination and consistent response schemas to collection endpoints where needed.
7. Evaluate Isolation Forest on a separate hold-out dataset and document honest metrics.
8. Add focused automated tests for calculation, detection and investigation workflows.
9. Improve configuration validation, logging, error handling and production security before any real deployment.

Authentication and authorization were not implemented in the audited version. Treat the application as a local demonstration unless appropriate access controls and operational safeguards are added.

## 11. Data Safety and Configuration

- Never commit `.env`, passwords, API keys or database credentials.
- Keep generated/private data out of the public repository unless it is safe and intended for publication.
- Provide `.env.example` with placeholder values only.
- Do not publish personal or sensitive information.
- Back up the local database before any destructive migration or data-generation operation.

## 12. AI Assistance Disclosure

AI tools were used for development assistance, technical guidance, debugging and documentation support. The candidate is responsible for reviewing the implementation, validating results, understanding design decisions and explaining known limitations.

The accompanying `docs/AI_PROMPT_HISTORY.md` records project-related prompts available from retained conversation records. Supplement it with prompts from other AI tools where applicable. Do not represent it as a complete verbatim export if those records are unavailable.

## 13. Repository Contents

The repository should contain the actual backend and frontend source, database migration files, dependency manifests, safe configuration examples, documentation and relevant supporting artifacts.

Suggested supporting documents:

```text
README.md
docs/
  architecture.md
  AI_PROMPT_HISTORY.md
  PROJECT_AUDIT.md
  screenshots/
.env.example
.gitignore
```

Only include files that exist and are relevant. Keep credentials, private datasets and local environment files out of the public repository.

---

**Project note:** StockGuard is a candidate project demonstrating inventory-data processing and shrinkage-detection concepts. Its synthetic-data results and local verification should not be interpreted as production validation or real-world model performance.