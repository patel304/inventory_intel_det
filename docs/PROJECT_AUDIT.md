StockGuard – Project Audit

**Project:** Inventory Shrinkage Detection System
**Purpose:** YottaFlex AI candidate project
**Audit baseline:** 31 October 2026
**Follow-up verification:** 1 November 2026

## 1. Executive Summary

StockGuard is a local inventory shrinkage detection application built with React, FastAPI, MySQL, SQLAlchemy and scikit-learn. The project contains a populated synthetic retail inventory dataset, inventory lookup, shrinkage alerts, investigation workflows and anomaly-detection functionality.

The application was further tested on 1 November 2026. The frontend production build completed successfully. ESLint reported no errors and one React Hook dependency warning. The inventory lookup endpoint returned HTTP 200 for Store ID `11` and SKU ID `201`; the frontend lookup was then tested successfully. The investigation save/close workflow and Shrinkage Alerts search-focus issue were also reported as fixed and working.

This report distinguishes the original source audit from subsequent checks. It does not claim that every item below has been re-audited after those changes.

## 2. Dataset Snapshot

The read-only database audit recorded:

| Table / entity | Row count |
|---|---:|
| Stores | 100 |
| SKUs | 5,000 |
| Inventory movements | 1,000,000 |
| Cycle counts | 20,000 |
| Employee roles | 4 |
| Shifts | 2 |
| Shrinkage alerts | 1,994 |
| Investigations | 2 |
| Investigation events | 2 |
| Returns | 0 |
| Promotions | 0 |
| Promotion-SKU mappings | 0 |

The audited movement types were opening balance, sale, receipt, damage, transfer out and transfer in. The audit found no populated adjustment or return movement rows.

Additional read-only integrity checks in the original audit reported:
- No unmatched transfer in/out group counts in the sampled check.
- No negative movement quantities in the sampled check.
- No alerts with null expected quantity or null cycle-count reference.
- 20,000 ground-truth rows, including 1,994 shrinkage labels.

The ground-truth file was located under `backend/data/generated/ground_truth.csv` and was gitignored at the time of the audit. Preserve the existing generated data; do not overwrite or regenerate it casually.

## 3. Follow-up Verification on 1 November 2026

| Check | Result | Evidence / note |
|---|---|---|
| `npm run build` | PASS | Vite production build completed successfully |
| `npm run lint` | PASS WITH WARNING | Zero errors; one missing `fetchAlerts` dependency warning in `App.jsx` |
| Store listing API | PASS | Returned store records; first displayed store ID was 11 |
| SKU listing API | PASS | Returned SKU records; first displayed SKU ID was 201 |
| Inventory lookup API | PASS | `GET /inventory/lookup?store_id=11&sku_id=201` returned HTTP 200 |
| Inventory Lookup UI | PASS | User confirmed successful frontend result |
| Investigation save/update and modal close | PASS | User confirmed working after the fix |
| Shrinkage Alerts search focus | PASS | User confirmed typing/focus issue fixed |

The inventory lookup response included `STORE-000001`, `SKU-000001`, expected stock `115.000`, and a latest cycle count of `108.000`. These values are from the local development database and may differ in another environment.

## 4. Original Audit Findings

The following items were identified during the 31 October source audit. They are retained here as findings to re-check against the current working tree, not as claims that they are all still present.

### 4.1 Inventory calculation

- The original audit found the expected-stock API was current-balance oriented and did not accept an `as_of` / `counted_at` filter.
- Movement sign rules were duplicated across inventory service, detection engine and data generation code.
- The original audit reported adjustment movement handling was inconsistent between the inventory service and detection engine.
- Historical expected-stock logic existed in the detection engine using movement timestamps.
- Transfer pairing was present in the generator and the audited live transfer groups were balanced.

**Recommended verification:** Confirm that all supported movement types use one consistent movement-sign definition and that historical stock is calculated at the relevant cycle-count timestamp.

### 4.2 Alerts

The original audit reported:
- A shortage threshold rule in the alert-detection endpoint.
- No duplicate guard in one alert-creation path.
- Differences between alert field names returned by the API and consumed by the frontend.
- Missing alert-detail endpoint in the audited version.
- Collection response and pagination improvements needed.

**Recommended verification:** Re-check duplicate handling, API/frontend field mappings, detail retrieval, pagination and alert identifiers in the current code.

### 4.3 Investigations

The original audit reported:
- Investigation creation and event creation were implemented.
- Duplicate investigation protection was missing.
- Resolving or closing an investigation did not synchronize the related alert status.
- Investigation event field naming differed between API and frontend expectations.
- The resolution column had a 100-character limit.

The save/update modal workflow was subsequently fixed and manually verified on 1 November. This UI fix does not by itself establish that alert-status synchronization, duplicate prevention or long-resolution handling are complete.

### 4.4 Detection engine and machine learning

The original audit reported:
- Rule-based shortage detection used a shortage threshold of 5 units.
- Isolation Forest was fitted and evaluated on the same rows rather than a separate hold-out set.
- Some model features overlapped with quantities used to generate synthetic labels.
- Consequently, recorded metrics may be optimistic and should not be presented as real-world predictive performance.

**Recommended verification:** Use a separate hold-out dataset or a carefully designed validation split. Document the synthetic label-generation process, features, split strategy and limitations. Do not claim general real-world model accuracy from synthetic data alone.

### 4.5 Frontend

The original audit reported issues with frontend field mapping, page coverage and configuration. Several pages and UI workflows were subsequently developed or tested. The following should be rechecked against the current frontend:
- Alert variance field mapping.
- Dashboard KPI source and calculation.
- API base URL configuration.
- Page-level loading, error and empty states.
- Page title and unused dependencies.
- Remaining React Hook dependency warning.

### 4.6 Security and operational readiness

The original audit noted:
- No authentication or authorization in the audited version.
- Local-development CORS configuration.
- Configuration validation and logging improvements needed.
- Database health endpoint error handling needed review.
- `.env.example` was empty at audit time.

StockGuard should therefore be described as a local demonstration / candidate project, not a production-hardened system.

## 5. Prioritized Remaining Work

The following are recommended priorities. Verify each item before changing code.

| Priority | Task | Reason |
|---|---|---|
| P0 | Re-check inventory movement sign consistency and historical stock calculations | Core business correctness |
| P0 | Validate alert and investigation lifecycle, including status synchronization and duplicate prevention | Workflow correctness |
| P0 | Review ML evaluation methodology and document limitations honestly | Avoid misleading model claims |
| P1 | Add focused tests for stock calculations, variance, alert creation and investigation updates | Regression protection |
| P1 | Re-check API/frontend field mappings and pagination | Data consistency and usability |
| P1 | Complete `.env.example` using actual configuration variable names | Reproducible local setup |
| P1 | Review `.gitignore` and confirm no credentials or private generated data are committed | Public repository safety |
| P2 | Improve logging, configuration validation and error handling | Maintainability |
| P2 | Consider authentication/authorization only if the intended deployment requires it | Production readiness |

Do not add features solely to make the project larger. Prioritize correctness, reproducibility, transparent limitations and the ability to explain the implementation.

## 6. Verification Commands

Run these from the relevant project directories:

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

### Backend

Start the backend using the repository's documented command, then verify the health endpoint and core APIs using the actual routes exposed by the running application.

Example inventory lookup:

```bash
curl -i "http://127.0.0.1:8000/inventory/lookup?store_id=11&sku_id=201"
```

Use IDs that exist in the target database. Do not assume IDs are always `1`.

## 7. Audit Limitations

- The original audit was a source inspection and read-only database review dated 31 October 2026.
- Follow-up checks on 1 November cover only the explicitly listed frontend build, lint, lookup and user-confirmed UI workflows.
- Other original audit findings have not all been independently re-tested after subsequent development.
- Synthetic dataset metrics are not evidence of performance on real retail data.
- This report does not certify production readiness, security compliance or real-world model effectiveness.

## 8. Final Assessment

StockGuard has a working local application flow and a substantial synthetic inventory dataset. The frontend build succeeds, inventory lookup has been verified end-to-end, and the reported UI regressions have been fixed.

The most important remaining work is not adding more screens. It is validating core inventory business rules, checking alert/investigation lifecycle consistency, improving model evaluation methodology, adding focused tests, and completing public-repository documentation and configuration safely.
