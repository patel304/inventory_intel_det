
import argparse
import csv
import random
from datetime import datetime, timedelta, time, timezone
from decimal import Decimal
from pathlib import Path

from app.database import SessionLocal
from app.models import (
    Store, SKU, EmployeeRole, Shift,
    InventoryMovement, CycleCount,
    Return, Promotion, PromotionSKU,
    ShrinkageAlert, Investigation, InvestigationEvent,
)

SEED = 20261022
BASE_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)

CATEGORIES = [
    "Grocery", "Beverages", "Personal Care",
    "Household", "Electronics", "Dairy",
]

OUTPUT_DIR = Path("data/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clear_existing_data(db):
    """Clear existing project data in foreign-key-safe order."""

    tables = [
        InvestigationEvent,
        Investigation,
        ShrinkageAlert,
        Return,
        CycleCount,
        InventoryMovement,
        PromotionSKU,
        Promotion,
        Shift,
        EmployeeRole,
        SKU,
        Store,
    ]

    for model in tables:
        db.query(model).delete(synchronize_session=False)

    db.flush()
    print("Existing project data cleared.")


def create_master_data(db, rng, num_stores, num_skus):
    stores = [
        Store(
            store_code=f"STORE-{i:06d}",
            name=f"Retail Store {i}",
            city=rng.choice(["Indore", "Bhopal", "Jaipur", "Delhi"]),
            state="India",
            is_active=True,
        )
        for i in range(1, num_stores + 1)
    ]

    skus = []

    for i in range(1, num_skus + 1):
        cost = Decimal(str(round(rng.uniform(10, 1000), 2)))

        skus.append(
            SKU(
                sku_code=f"SKU-{i:06d}",
                name=f"Product {i}",
                category=rng.choice(CATEGORIES),
                unit_cost=cost,
                unit_price=(cost * Decimal("1.30")).quantize(
                    Decimal("0.01")
                ),
                is_active=True,
            )
        )

    roles = [
        EmployeeRole(role_code="MANAGER", role_name="Store Manager"),
        EmployeeRole(role_code="CASHIER", role_name="Cashier"),
        EmployeeRole(role_code="STOCK", role_name="Stock Associate"),
        EmployeeRole(role_code="AUDITOR", role_name="Inventory Auditor"),
    ]

    shifts = [
        Shift(
            shift_code="MORNING",
            shift_name="Morning Shift",
            start_time=time(6, 0),
            end_time=time(14, 0),
        ),
        Shift(
            shift_code="EVENING",
            shift_name="Evening Shift",
            start_time=time(14, 0),
            end_time=time(22, 0),
        ),
    ]

    db.add_all(stores + skus + roles + shifts)
    db.flush()

    return stores, skus, roles, shifts


def generate_movements(
    db, rng, stores, skus, roles, shifts, target_movements
):
    balances = {}
    movement_count = 0
    batch = []
    movement_number = 0
    transfer_number = 0
    current_time = BASE_DATE

    def add_movement(
        store_id, sku_id, movement_type, quantity,
        role_id, shift_id, transfer_group_id=None,
    ):
        nonlocal movement_number, movement_count, batch

        movement_number += 1
        movement_count += 1

        batch.append(
            InventoryMovement(
                movement_code=f"MOV-2026-{movement_number:08d}",
                store_id=store_id,
                sku_id=sku_id,
                employee_role_id=role_id,
                shift_id=shift_id,
                movement_type=movement_type,
                quantity=Decimal(str(quantity)),
                reference_code=f"REF-{movement_number:08d}",
                transfer_group_id=transfer_group_id,
                effective_at=current_time,
                recorded_at=current_time + timedelta(
                    minutes=rng.randint(0, 30)
                ),
                source_system="SYNTHETIC",
            )
        )

        if len(batch) >= 1000:
            db.add_all(batch)
            db.flush()
            batch = []

    print("Generating opening balances...")

    # Every store-SKU combination starts with opening stock.
    for store in stores:
        for sku in skus:
            key = (store.id, sku.id)
            opening = rng.randint(40, 150)
            balances[key] = opening

            add_movement(
                store.id, sku.id, "OPENING_BALANCE",
                opening, roles[0].id, shifts[0].id,
            )

    if batch:
        db.add_all(batch)
        db.flush()
        batch = []

    print("Generating realistic inventory movements...")

    while movement_count < target_movements:
        current_time += timedelta(minutes=rng.randint(1, 60))

        store = rng.choice(stores)
        sku = rng.choice(skus)
        key = (store.id, sku.id)

        role = rng.choice(roles)
        shift = rng.choice(shifts)
        stock = balances[key]

        operation = rng.choices(
            ["SALE", "RECEIPT", "DAMAGE", "TRANSFER"],
            weights=[55, 25, 10, 10],
        )[0]

        quantity = rng.randint(1, min(10, max(stock, 1)))

        if operation == "SALE" and stock >= quantity:
            add_movement(
                store.id, sku.id, "SALE", quantity,
                role.id, shift.id,
            )
            balances[key] -= quantity

        elif operation == "DAMAGE" and stock >= quantity:
            add_movement(
                store.id, sku.id, "DAMAGE", quantity,
                role.id, shift.id,
            )
            balances[key] -= quantity

        elif operation == "TRANSFER" and movement_count + 2 <= target_movements:
            destination = rng.choice(
                [s for s in stores if s.id != store.id]
            )

            transfer_number += 1
            transfer_id = f"TRF-{transfer_number:08d}"

            add_movement(
                store.id, sku.id, "TRANSFER_OUT", quantity,
                role.id, shift.id, transfer_id,
            )

            add_movement(
                destination.id, sku.id, "TRANSFER_IN", quantity,
                role.id, shift.id, transfer_id,
            )

            balances[key] -= quantity
            balances[(destination.id, sku.id)] += quantity

        else:
            quantity = rng.randint(5, 25)

            add_movement(
                store.id, sku.id, "RECEIPT", quantity,
                role.id, shift.id,
            )
            balances[key] += quantity

    if batch:
        db.add_all(batch)
        db.flush()

    print(f"Created {movement_count:,} movements.")
    return balances


def generate_cycle_counts(
    db, rng, stores, skus, roles, shifts,
    balances, num_counts,
):
    print("Generating cycle counts and shrinkage ground truth...")

    combinations = [
        (store, sku)
        for store in stores
        for sku in skus
    ]

    rng.shuffle(combinations)
    combinations = combinations[:num_counts]

    ground_truth = []
    batch = []

    for i, (store, sku) in enumerate(combinations, start=1):
        expected = balances[(store.id, sku.id)]

        # Inject controlled stock shortages in 10% of counts.
        is_shrinkage = rng.random() < 0.10

        missing_quantity = (
            rng.randint(5, min(20, expected))
            if is_shrinkage and expected >= 5
            else 0
        )

        observed = expected - missing_quantity

        counted_at = current_count_time = (
            BASE_DATE + timedelta(days=300)
        )

        count = CycleCount(
            count_code=f"CNT-2026-{i:06d}",
            store_id=store.id,
            sku_id=sku.id,
            employee_role_id=roles[3].id,
            shift_id=shifts[0].id,
            counted_quantity=Decimal(str(observed)),
            counted_at=counted_at,
            recorded_at=counted_at + timedelta(minutes=5),
            count_status="COMPLETED",
        )

        batch.append(count)

        ground_truth.append({
            "count_code": count.count_code,
            "store_code": store.store_code,
            "sku_code": sku.sku_code,
            "expected_quantity": expected,
            "observed_quantity": observed,
            "missing_quantity": missing_quantity,
            "is_shrinkage": int(missing_quantity > 0),
        })

        if len(batch) >= 500:
            db.add_all(batch)
            db.flush()
            batch = []

    if batch:
        db.add_all(batch)
        db.flush()

    output_file = OUTPUT_DIR / "ground_truth.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(ground_truth[0].keys()),
        )
        writer.writeheader()
        writer.writerows(ground_truth)

    print(f"Ground truth saved: {output_file}")
    print(
        "Injected shrinkage cases:",
        sum(row["is_shrinkage"] for row in ground_truth),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    rng = random.Random(SEED)

    if args.full:
        num_stores = 100
        num_skus = 5000
        num_movements = 1_000_000
        num_counts = 20_000
    else:
        num_stores = 5
        num_skus = 100
        num_movements = 5000
        num_counts = 500

    db = SessionLocal()

    try:
        if db.query(Store).count() > 0:
            if not args.reset:
                raise RuntimeError(
                    "Existing data found. Use --reset to regenerate."
                )

            clear_existing_data(db)

        print("Starting inventory data generation...")
        print(f"Mode: {'FULL' if args.full else 'STARTER'}")

        stores, skus, roles, shifts = create_master_data(
            db, rng, num_stores, num_skus
        )

        balances = generate_movements(
            db, rng, stores, skus, roles, shifts,
            num_movements,
        )

        generate_cycle_counts(
            db, rng, stores, skus, roles, shifts,
            balances, num_counts,
        )

        db.commit()

        print("\nDATA GENERATION COMPLETED")
        print("Stores:", db.query(Store).count())
        print("SKUs:", db.query(SKU).count())
        print("Movements:", db.query(InventoryMovement).count())
        print("Cycle counts:", db.query(CycleCount).count())

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
