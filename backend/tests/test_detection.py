from decimal import Decimal
from pathlib import Path

from app.models import CycleCount
from app.services.detection_engine import evaluate_predictions, run_detection
from app.services.inventory_service import calculate_expected_stock


def test_evaluate_predictions_includes_accuracy():
    metrics = evaluate_predictions([0, 1, 1, 0], [0, 1, 0, 0])
    assert "accuracy" in metrics
    assert metrics["confusion_matrix"] == [[2, 0], [1, 1]]


def test_run_detection_holdout_and_no_label_features(db, seeded, tmp_path: Path):
    store = seeded["store_a"]
    sku = seeded["sku"]
    expected = calculate_expected_stock(db, store.id, sku.id, as_of=seeded["count"].counted_at)

    extra = []
    for index in range(8):
        is_shrinkage = index < 4
        counted = expected - Decimal("10") if is_shrinkage else expected
        extra.append(
            CycleCount(
                count_code=f"CNT-X-{index}",
                store_id=store.id,
                sku_id=sku.id,
                counted_quantity=counted,
                counted_at=seeded["count"].counted_at,
                recorded_at=seeded["count"].recorded_at,
                count_status="COMPLETED",
            )
        )
    db.add_all(extra)
    db.flush()

    truth_path = tmp_path / "ground_truth.csv"
    rows = ["count_code,is_shrinkage"]
    rows.append("CNT-1,0")
    for index in range(8):
        rows.append(f"CNT-X-{index},{1 if index < 4 else 0}")
    truth_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    result = run_detection(
        db,
        shortage_threshold=5,
        persist_alerts=False,
        ground_truth_path=truth_path,
        output_dir=tmp_path,
    )
    assert result["records_evaluated"] == 9
    assert "precision" in result["rule_based"]
    assert "accuracy" in result["isolation_forest"]
    assert result["alert_summary"]["persisted"] is False
    assert (tmp_path / "model_metrics.json").exists()
