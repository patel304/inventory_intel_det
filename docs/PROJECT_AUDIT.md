# StockGuard Project Audit

**Audit date:** 2026-10-31  
**Branch:** `main` @ `d26bb9c` (working tree was clean at audit start)  
**Method:** Source inspection, documentation review, and read-only MySQL queries. No records were modified.

Status legend used below:

| Status | Meaning |
| --- | --- |
| Implemented | Code exists and matches the intended design |
| Tested and working | Exercised against the live database or passing automated tests |
| Implemented but untested | Code exists; no automated test and not verified in this audit |
| Partially implemented | Core path exists; important cases missing |
| Missing | Required for the product, not present |
| Broken | Incorrect, unsafe, or will fail in normal use |

---

## 1. Verified live database (read-only)

| Table | Row count | Notes |
| --- | --- | --- |
| stores | 100 | Matches stated full dataset |
| skus | 5,000 | Matches stated full dataset |
| inventory_movements | 1,000,000 | Preserved; do not regenerate |
| cycle_counts | 20,000 | Preserved |
| employee_roles | 4 | |
| shifts | 2 | |
| shrinkage_alerts | 1,994 | All have `cycle_count_id` and expected/observed/variance |
| investigations | 2 | Both `IN_PROGRESS` |
| investigation_events | 2 | |
| returns | 0 | Table exists, unused |
| promotions | 0 | Table exists, unused |
| promotion_skus | 0 | Table exists, unused |
| alembic_version | 1 | Single migration `6c8916762d8e` |

Movement type mix (live):

- OPENING_BALANCE 500,000
- SALE 249,789
- RECEIPT 114,159
- DAMAGE 45,370
- TRANSFER_OUT 45,341
- TRANSFER_IN 45,341

No `ADJUSTMENT_IN` / `ADJUSTMENT_OUT` / `RETURN_IN` rows exist in the current dataset.

Read-only integrity samples:

- Transfer groups with unmatched IN/OUT counts: **0**
- Negative movement quantities: **0**
- Alerts with NULL expected quantity: **0**
- Alerts with NULL cycle_count_id: **0**
- Duplicate `count_code` in `ground_truth.csv`: **0**
- Ground-truth rows: **20,000**; shrinkage labels: **1,994**

Ground truth file present at `backend/data/generated/ground_truth.csv` (gitignored). **Do not overwrite.**

---

## 2. Repository and documentation

| Item | Status | Evidence |
| --- | --- | --- |
| README.md | Missing | File is empty |
| ASSUMPTIONS.md | Missing | File is empty |
| LIMITATIONS.md | Missing | File is empty |
| PROMPT_HISTORY.md | Missing | File is empty |
| docs/architecture.md | Partially implemented | Entities, inventory equation, seed; omits APIs, frontend, evaluation caveats |
| .env.example | Missing | Empty file at repo root |
| .gitignore | Implemented | Ignores `.env`, venv, `data/generated/`, node_modules |
| requirements.txt | Partially implemented | Full pip freeze including unrelated packages (`agent-detector`, OpenTelemetry, Sentry) |
| Automated tests | Missing | No `tests/` directory, no pytest config |
| Alembic migration | Implemented | 12 business tables + alembic_version |

---

## 3. Backend

### 3.1 Application shell

| Item | Status | Notes |
| --- | --- | --- |
| FastAPI app | Implemented but untested | `backend/app/main.py` |
| CORS | Partially implemented | Hardcoded localhost Vite origins only |
| Settings | Partially implemented | `python-dotenv` + `os.getenv`; no validation; engine created at import |
| Session management | Partially implemented | `get_db` closes session; no rollback on exception |
| Health `/health` | Implemented but untested | Always 200 |
| Health `/health/database` | Partially implemented | Returns 200 with `"status": "error"` on failure; may leak driver messages |
| Pydantic request models | Partially implemented | Variance + investigation bodies only |
| Consistent response schemas | Missing | Mix of dicts and ORM objects |
| Pagination | Missing | `/alerts` and `/investigations` return full collections |
| Logging | Missing | |
| Exception handling | Partially implemented | Bare `except: rollback; raise` on a few writes |
| AuthN/AuthZ | Missing | Not claimed; internal academic demo |

### 3.2 Inventory calculation

| Item | Status | Notes |
| --- | --- | --- |
| Expected stock API | Partially implemented | Current-balance only; **no `as_of` / `counted_at` filter** |
| Increase types in API service | Broken / incomplete | `inventory_service.py` omits `ADJUSTMENT_IN` / `ADJUSTMENT_OUT` (detection engine includes them) |
| Historical expected stock | Implemented in detection only | `detection_engine.load_inventory_data` filters `effective_at <= counted_at` |
| Transfer pairing | Implemented in generator | Paired TRANSFER_OUT/IN with `transfer_group_id`; live counts match |
| Treating transfers as shrinkage | Implemented correctly | Transfers change location stock, not shrinkage |
| Variance API | Implemented but untested | `counted - expected`; types SHORTAGE / SURPLUS / MATCHED |

Duplicate business logic: movement sign rules exist in `inventory_service.py`, `detection_engine.py`, and `generate_data.py`.

### 3.3 Alerts

| Item | Status | Notes |
| --- | --- | --- |
| POST `/alerts/detect` | Partially implemented | Creates alert for shortage ≥ 5; no duplicate guard; no `cycle_count_id`; uses `count()` for alert numbers (race-prone) |
| GET `/alerts` | Partially implemented | Filter by status only; omits detection_rule, confidence, cycle_count_id |
| GET `/alerts/{id}` | Missing | |
| Frontend field mapping | Broken | UI reads `alert.variance`; API returns `variance_quantity` |
| Persist from batch detection | Implemented | Skips existing `cycle_count_id` + `RULE_BASED_SHORTAGE` |
| NULL historical fields | Tested and working (live) | Existing alerts are populated; do not backfill invented values |

### 3.4 Investigations

| Item | Status | Notes |
| --- | --- | --- |
| POST `/investigations` | Partially implemented | Creates investigation, sets alert `INVESTIGATING`, writes start event |
| Duplicate investigations | Missing | No uniqueness; a second POST creates another row |
| GET `/investigations` | Partially implemented | Returns ORM models, no pagination, no alert code |
| PUT `/investigations/{id}` | Partially implemented | Required findings/resolution/status; does **not** update alert status on resolve/close |
| Event history | Implemented but untested | GET events; frontend expects `event.id`, API returns `event_id` |
| Assign investigator after create | Missing | Only `assigned_to` on create |
| `resolution` column | Partially implemented | Schema is `String(100)`; long notes will fail at DB |

Schema change would be required to widen `resolution`. **Not done** (needs approval).

### 3.5 Catalog / dashboard APIs

| Item | Status |
| --- | --- |
| Stores list | Missing |
| SKU list | Missing |
| Dashboard aggregate counts | Missing |
| Analytics aggregates | Missing |
| Model metrics API | Missing |
| Cycle count listing | Missing |

---

## 4. Detection engine and ML

| Item | Status | Notes |
| --- | --- | --- |
| Rule-based shortage | Implemented | `shortage >= 5` |
| Isolation Forest | Partially implemented | Fits and scores the **same** rows (no hold-out) |
| Features | Partially implemented | variance, shortage_ratio, unit_cost, estimated_loss; no movement frequency |
| Target leakage | Broken (evaluation) | Labels never used as features (good), but features are the same quantities used to **generate** synthetic labels |
| Accuracy metric | Missing | Precision/recall/F1/FPR/confusion only |
| Recorded metrics | Implemented | `model_metrics.csv`: Rule-based P/R/F1 = 1.0; Isolation Forest F1 ≈ 0.9992 |
| Metric integrity | Broken as a real-world claim | Perfect rule score is expected: generator injects shortage ≥ 5 iff `is_shrinkage=1` |
| Ground truth path | Partially implemented | Relative `data/generated/...` depends on process cwd |
| Batch join performance | Partially implemented | Per-count SQL join against 1M movements is likely too heavy to re-run casually |

---

## 5. Frontend

| Item | Status | Notes |
| --- | --- | --- |
| React + Vite + Tailwind | Implemented | |
| Sidebar + alerts + investigations | Partially implemented | Single `App.jsx` |
| Dashboard KPIs | Partially implemented | Derived from loaded alerts only; hardcoded “Detection Engine Active” |
| Stores / Products / Inventory / Model / Health pages | Missing | |
| Charts | Partially implemented | CSS bars only; `recharts` unused |
| API base URL | Partially implemented | Hardcoded `http://127.0.0.1:8000` |
| Loading / error / empty | Implemented but untested | |
| Variance column | Broken | Wrong field name |
| Page title | Partially implemented | `index.html` title is “frontend” |
| Frontend tests | Missing | |
| Secrets in frontend | Implemented correctly | None found |

---

## 6. Data generation

| Item | Status | Notes |
| --- | --- | --- |
| Incremental `--append-full` | Implemented | Refuses to run without flag; no `--reset` in current script |
| Seed 20261022 | Implemented | |
| Transfer pairing | Implemented | |
| Shrinkage injection ~10% | Implemented | Missing qty 5–20 when expected ≥ 5 |
| Returns / promotions | Missing (data) | Models exist; generator does not populate |
| Faker | Missing | Listed in stack; generator uses `random` only |

---

## 7. Security and quality

| Item | Status | Notes |
| --- | --- | --- |
| SQL injection | Implemented (good) | SQLAlchemy bound parameters |
| Credentials | Implemented (good) | Live `.env` gitignored; example file empty |
| Alembic URL | Partially implemented | `hide_password=False` when rendering URL |
| CORS credentials + wildcard methods | Partially implemented | Fine for local demo; not production-hardened |
| Input validation | Partially implemented | Some numeric floors; missing enums/length limits |
| Error leakage | Partially implemented | DB health returns raw exception text |

---

## 8. Performance

| Item | Status | Notes |
| --- | --- | --- |
| Movement composite index | Implemented | `(store_id, sku_id, effective_at)` |
| Alert list of ~2k rows | Acceptable | Should still paginate |
| Loading 1M movements in the browser | Not present (good) | Must not be added |
| Detection historical join | Risk | Needs an in-memory/prefix-sum approach, not a 20k×1M SQL join |
| N+1 on alert list | Low | Single query; missing joins for store/SKU names |

---

## 9. Priority gaps (for implementation)

1. Unify inventory equation (adjustments + as-of timestamp) between API and detection.
2. Complete alert/investigation APIs (detail, pagination, duplicate guards, alert status sync).
3. Dashboard/catalog/analytics/metrics endpoints using real counts.
4. Isolation Forest hold-out evaluation + honest metrics documentation.
5. Frontend pages wired to those APIs; fix field mappings.
6. Isolated automated tests (SQLite), never against the MySQL dataset.
7. Documentation and GitHub hygiene (`.env.example`, README, requirements).

No schema migration is required for the above if `resolution` notes stay ≤ 100 characters (documented limitation).
