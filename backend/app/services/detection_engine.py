import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import BACKEND_ROOT
from app.inventory_math import signed_quantity
from app.models import CycleCount, InventoryMovement, SKU, ShrinkageAlert

OUTPUT_DIR = BACKEND_ROOT / "data" / "generated"
GROUND_TRUTH_PATH = OUTPUT_DIR / "ground_truth.csv"
SEED = 20261022


def calculate_fpr(actual, predicted) -> float:
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()
    return float(round(fp / (fp + tn) if (fp + tn) else 0.0, 4))


def evaluate_predictions(actual, predicted) -> dict:
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    return {
        "precision": float(round(precision_score(actual, predicted, zero_division=0), 4)),
        "recall": float(round(recall_score(actual, predicted, zero_division=0), 4)),
        "f1_score": float(round(f1_score(actual, predicted, zero_division=0), 4)),
        "accuracy": float(round(accuracy_score(actual, predicted), 4)),
        "false_positive_rate": calculate_fpr(actual, predicted),
        "confusion_matrix": matrix.tolist(),
    }


def load_inventory_data(db: Session) -> pd.DataFrame:
    """
    Expected stock as of each cycle count's counted_at.

    Movements with effective_at after counted_at are excluded.
    Implemented with per-(store, sku) prefix sums so a full 1M-row
    movement table does not require a 20k-way SQL join.
    """
    counts = db.query(CycleCount).order_by(CycleCount.id).all()
    if not counts:
        return pd.DataFrame()

    skus = {sku.id: sku for sku in db.query(SKU).all()}

    events = defaultdict(list)
    stmt = select(
        InventoryMovement.store_id,
        InventoryMovement.sku_id,
        InventoryMovement.effective_at,
        InventoryMovement.movement_type,
        InventoryMovement.quantity,
    )
    for store_id, sku_id, effective_at, movement_type, quantity in db.execute(stmt).yield_per(10000):
        events[(store_id, sku_id)].append(
            (effective_at, float(signed_quantity(movement_type, quantity)))
        )

    timelines = {}
    for key, rows in events.items():
        rows.sort(key=lambda item: item[0])
        times = []
        prefix = []
        running = 0.0
        counts_at = []
        n = 0
        for effective_at, qty in rows:
            running += qty
            n += 1
            times.append(effective_at)
            prefix.append(running)
            counts_at.append(n)
        timelines[key] = (times, prefix, counts_at)

    def balance_as_of(store_id, sku_id, counted_at):
        timeline = timelines.get((store_id, sku_id))
        if not timeline:
            return 0.0, 0
        times, prefix, counts_at = timeline
        lo, hi = 0, len(times)
        while lo < hi:
            mid = (lo + hi) // 2
            if times[mid] <= counted_at:
                lo = mid + 1
            else:
                hi = mid
        if lo == 0:
            return 0.0, 0
        return prefix[lo - 1], counts_at[lo - 1]

    records = []
    for count in counts:
        expected, movement_frequency = balance_as_of(
            count.store_id, count.sku_id, count.counted_at
        )
        observed = float(count.counted_quantity)
        variance = observed - expected
        shortage = max(0.0, expected - observed)
        sku = skus.get(count.sku_id)
        unit_cost = float(sku.unit_cost) if sku else 0.0
        shortage_ratio = shortage / expected if expected > 0 else 0.0
        records.append({
            "cycle_count_id": count.id,
            "count_code": count.count_code,
            "store_id": count.store_id,
            "sku_id": count.sku_id,
            "counted_at": count.counted_at,
            "expected_quantity": expected,
            "observed_quantity": observed,
            "variance": variance,
            "shortage": shortage,
            "shortage_ratio": shortage_ratio,
            "unit_cost": unit_cost,
            "estimated_loss": shortage * unit_cost,
            "movement_frequency": movement_frequency,
        })

    return pd.DataFrame(records)


def persist_shrinkage_alerts(db: Session, df: pd.DataFrame) -> dict:
    created = 0
    skipped = 0
    detected_rows = df[df["rule_prediction"] == 1]

    try:
        for _, row in detected_rows.iterrows():
            cycle_count_id = int(row["cycle_count_id"])
            existing = (
                db.query(ShrinkageAlert)
                .filter(
                    ShrinkageAlert.cycle_count_id == cycle_count_id,
                    ShrinkageAlert.detection_rule == "RULE_BASED_SHORTAGE",
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            shortage = float(row["shortage"])
            severity = "HIGH" if shortage >= 20 else "MEDIUM"
            alert = ShrinkageAlert(
                alert_code=f"SHR-AUTO-{cycle_count_id:06d}",
                store_id=int(row["store_id"]),
                sku_id=int(row["sku_id"]),
                cycle_count_id=cycle_count_id,
                detection_rule="RULE_BASED_SHORTAGE",
                severity=severity,
                confidence_score=1.0,
                expected_quantity=row["expected_quantity"],
                observed_quantity=row["observed_quantity"],
                variance_quantity=row["variance"],
                status="OPEN",
                detected_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(alert)
            created += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"alerts_created": created, "duplicates_skipped": skipped}


def run_detection(
    db: Session,
    shortage_threshold: float = 5,
    persist_alerts: bool = True,
    ground_truth_path: Path | None = None,
    output_dir: Path | None = None,
) -> dict:
    output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    truth_path = Path(ground_truth_path) if ground_truth_path else GROUND_TRUTH_PATH

    df = load_inventory_data(db)
    if df.empty:
        raise ValueError("No cycle count data found.")

    if not truth_path.exists():
        raise FileNotFoundError(f"Ground truth not found: {truth_path}")

    truth = pd.read_csv(truth_path)
    required_columns = {"count_code", "is_shrinkage"}
    missing_columns = required_columns - set(truth.columns)
    if missing_columns:
        raise ValueError(f"Ground truth is missing columns: {sorted(missing_columns)}")
    if truth["count_code"].duplicated().any():
        raise ValueError("Duplicate count_code values found in ground_truth.csv.")

    df = df.merge(
        truth[["count_code", "is_shrinkage"]],
        on="count_code",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    unmatched = int((df["_merge"] != "both").sum())
    if unmatched:
        raise ValueError(f"{unmatched} cycle counts have no matching ground-truth row.")
    df = df.drop(columns=["_merge"])
    if df["is_shrinkage"].isna().any():
        raise ValueError("Ground-truth labels contain missing values.")

    actual = df["is_shrinkage"].astype(int)
    df["rule_prediction"] = (df["shortage"] >= shortage_threshold).astype(int)
    rule_metrics = evaluate_predictions(actual, df["rule_prediction"])
    rule_metrics["evaluation"] = "full_labelled_set_no_training"

    features = [
        "variance",
        "shortage_ratio",
        "unit_cost",
        "estimated_loss",
        "movement_frequency",
    ]
    feature_data = (
        df[features]
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
    )

    if len(df) < 4 or actual.nunique() < 2:
        # Tiny fixtures: fit on all rows but still record the limitation.
        model = IsolationForest(
            n_estimators=100,
            contamination=0.10,
            random_state=SEED,
            n_jobs=1,
        )
        model.fit(feature_data)
        df["ml_prediction"] = (model.predict(feature_data) == -1).astype(int)
        df["ml_split"] = "all"
        ml_metrics = evaluate_predictions(actual, df["ml_prediction"])
        ml_metrics["evaluation"] = "insufficient_rows_for_holdout"
        ml_metrics["train_size"] = len(df)
        ml_metrics["test_size"] = 0
    else:
        idx_train, idx_test = train_test_split(
            df.index,
            test_size=0.30,
            random_state=SEED,
            stratify=actual,
        )
        model = IsolationForest(
            n_estimators=200,
            contamination=0.10,
            random_state=SEED,
            n_jobs=-1,
        )
        model.fit(feature_data.loc[idx_train])
        df["ml_prediction"] = 0
        df.loc[idx_train, "ml_prediction"] = (
            model.predict(feature_data.loc[idx_train]) == -1
        ).astype(int)
        df.loc[idx_test, "ml_prediction"] = (
            model.predict(feature_data.loc[idx_test]) == -1
        ).astype(int)
        df["ml_split"] = "train"
        df.loc[idx_test, "ml_split"] = "test"
        ml_metrics = evaluate_predictions(
            actual.loc[idx_test],
            df.loc[idx_test, "ml_prediction"].astype(int),
        )
        ml_metrics["evaluation"] = "holdout_30pct_stratified"
        ml_metrics["train_size"] = int(len(idx_train))
        ml_metrics["test_size"] = int(len(idx_test))

    df.to_csv(output_dir / "detection_results.csv", index=False)

    summary_rows = [
        {
            "model": "Rule Based",
            **{key: value for key, value in rule_metrics.items() if key != "confusion_matrix"},
        },
        {
            "model": "Isolation Forest",
            **{key: value for key, value in ml_metrics.items() if key != "confusion_matrix"},
        },
    ]
    pd.DataFrame(summary_rows).to_csv(output_dir / "model_metrics.csv", index=False)

    payload = {
        "synthetic_data": True,
        "disclaimer": (
            "Metrics are computed on synthetic cycle counts. "
            "They are not real-world production accuracy. "
            "Rule-based scores can be perfect because labels were injected "
            "using the same shortage threshold used by the detector."
        ),
        "source": str(output_dir / "model_metrics.json"),
        "records_evaluated": int(len(df)),
        "actual_shrinkage_cases": int(actual.sum()),
        "models": [
            {"model": "Rule Based", **rule_metrics},
            {"model": "Isolation Forest", **ml_metrics},
        ],
        "features": features,
        "seed": SEED,
    }
    (output_dir / "model_metrics.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    alert_summary = {"alerts_created": 0, "duplicates_skipped": 0, "persisted": False}
    if persist_alerts:
        alert_summary = persist_shrinkage_alerts(db, df)
        alert_summary["persisted"] = True

    return {
        "records_evaluated": len(df),
        "actual_shrinkage_cases": int(actual.sum()),
        "rule_based": rule_metrics,
        "isolation_forest": ml_metrics,
        "alert_summary": alert_summary,
        "results_file": str(output_dir / "detection_results.csv"),
        "metrics_file": str(output_dir / "model_metrics.csv"),
    }
