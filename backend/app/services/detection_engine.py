from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import and_, case, func
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from app.models import (
    CycleCount,
    InventoryMovement,
    SKU,
    ShrinkageAlert,
)

GROUND_TRUTH_PATH = Path("data/generated/ground_truth.csv")
OUTPUT_DIR = Path("data/generated")
SEED = 20261022

INCREASE_TYPES = {
    "OPENING_BALANCE",
    "RECEIPT",
    "RETURN_IN",
    "TRANSFER_IN",
    "ADJUSTMENT_IN",
}
DECREASE_TYPES = {
    "SALE",
    "DAMAGE",
    "TRANSFER_OUT",
    "ADJUSTMENT_OUT",
}


# --------------------------------------------------
# 1. LOAD HISTORICAL INVENTORY DATA
# --------------------------------------------------

def load_inventory_data(db):
    """
    Calculate expected stock as of each cycle count's counted_at time.

    Important: movements recorded/effective after a count are excluded
    from that count's expected stock.
    """

    counts = db.query(CycleCount).order_by(CycleCount.id).all()

    if not counts:
        return pd.DataFrame()

    skus = {
        sku.id: sku
        for sku in db.query(SKU).all()
    }

    signed_quantity = case(
        (
            InventoryMovement.movement_type.in_(INCREASE_TYPES),
            InventoryMovement.quantity,
        ),
        (
            InventoryMovement.movement_type.in_(DECREASE_TYPES),
            -InventoryMovement.quantity,
        ),
        else_=0,
    )

    # One aggregate per cycle count. The timestamp condition is essential:
    # later movements must not change the expected stock of an earlier count.
    balance_rows = (
        db.query(
            CycleCount.id.label("cycle_count_id"),
            func.coalesce(func.sum(signed_quantity), 0).label(
                "expected_quantity"
            ),
        )
        .outerjoin(
            InventoryMovement,
            and_(
                InventoryMovement.store_id == CycleCount.store_id,
                InventoryMovement.sku_id == CycleCount.sku_id,
                InventoryMovement.effective_at <= CycleCount.counted_at,
            ),
        )
        .group_by(CycleCount.id)
        .all()
    )

    expected_by_count = {
        int(row.cycle_count_id): float(row.expected_quantity or 0)
        for row in balance_rows
    }

    records = []

    for count in counts:
        expected = expected_by_count.get(count.id, 0.0)
        observed = float(count.counted_quantity)

        # Positive variance means overage; negative means shortage.
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
        })

    return pd.DataFrame(records)


# --------------------------------------------------
# 2. FALSE POSITIVE RATE
# --------------------------------------------------

def calculate_fpr(actual, predicted):
    tn, fp, fn, tp = confusion_matrix(
        actual,
        predicted,
        labels=[0, 1],
    ).ravel()

    return float(round(fp / (fp + tn) if (fp + tn) else 0.0, 4))


# --------------------------------------------------
# 3. MODEL EVALUATION
# --------------------------------------------------

def evaluate_predictions(actual, predicted):
    return {
        "precision": float(round(
            precision_score(actual, predicted, zero_division=0), 4
        )),
        "recall": float(round(
            recall_score(actual, predicted, zero_division=0), 4
        )),
        "f1_score": float(round(
            f1_score(actual, predicted, zero_division=0), 4
        )),
        "false_positive_rate": calculate_fpr(actual, predicted),
        "confusion_matrix": confusion_matrix(
            actual,
            predicted,
            labels=[0, 1],
        ).tolist(),
    }


# --------------------------------------------------
# 4. SAVE ALERTS TO MYSQL
# --------------------------------------------------

def persist_shrinkage_alerts(db, df):
    """Persist rule-based detections and skip existing matching alerts."""

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
                detected_at=datetime.now(timezone.utc),
            )

            db.add(alert)
            created += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "alerts_created": created,
        "duplicates_skipped": skipped,
    }


# --------------------------------------------------
# 5. COMPLETE DETECTION PIPELINE
# --------------------------------------------------

def run_detection(db, shortage_threshold=5):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_inventory_data(db)

    if df.empty:
        raise ValueError("No cycle count data found.")

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground truth not found: {GROUND_TRUTH_PATH}"
        )

    truth = pd.read_csv(GROUND_TRUTH_PATH)

    required_columns = {"count_code", "is_shrinkage"}
    missing_columns = required_columns - set(truth.columns)
    if missing_columns:
        raise ValueError(
            f"Ground truth is missing columns: {sorted(missing_columns)}"
        )

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
        raise ValueError(
            f"{unmatched} cycle counts have no matching ground-truth row."
        )

    df = df.drop(columns=["_merge"])

    if df["is_shrinkage"].isna().any():
        raise ValueError("Ground-truth labels contain missing values.")

    actual = df["is_shrinkage"].astype(int)

    # Ground truth is used only as the evaluation label, never as a feature.
    df["rule_prediction"] = (
        df["shortage"] >= shortage_threshold
    ).astype(int)

    rule_metrics = evaluate_predictions(actual, df["rule_prediction"])

    features = [
        "variance",
        "shortage_ratio",
        "unit_cost",
        "estimated_loss",
    ]

    feature_data = df[features].replace(
        [float("inf"), float("-inf")], 0
    ).fillna(0)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.10,
        random_state=SEED,
        n_jobs=-1,
    )

    model.fit(feature_data)

    df["ml_prediction"] = (
        model.predict(feature_data) == -1
    ).astype(int)

    ml_metrics = evaluate_predictions(actual, df["ml_prediction"])

    # Persist detailed predictions and metrics.
    df.to_csv(OUTPUT_DIR / "detection_results.csv", index=False)

    summary = pd.DataFrame([
        {
            "model": "Rule Based",
            **{
                key: value
                for key, value in rule_metrics.items()
                if key != "confusion_matrix"
            },
        },
        {
            "model": "Isolation Forest",
            **{
                key: value
                for key, value in ml_metrics.items()
                if key != "confusion_matrix"
            },
        },
    ])

    summary.to_csv(OUTPUT_DIR / "model_metrics.csv", index=False)

    # Only rule-based alerts are persisted, matching the existing design.
    alert_summary = persist_shrinkage_alerts(db, df)

    return {
        "records_evaluated": len(df),
        "actual_shrinkage_cases": int(actual.sum()),
        "rule_based": rule_metrics,
        "isolation_forest": ml_metrics,
        "alert_summary": alert_summary,
        "results_file": str(OUTPUT_DIR / "detection_results.csv"),
        "metrics_file": str(OUTPUT_DIR / "model_metrics.csv"),
    }