import argparse
import csv
import random
from datetime import datetime, timedelta, time, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func

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


def next_code_number(db, model, column):
    """Return the next numeric suffix for a business-code column."""
    values = db.query(column).all()
    highest = 0
    for (value,) in values:
        if value:
            try:
                highest = max(highest, int(value.rsplit("-", 1)[-1]))
            except (ValueError, AttributeError):
                continue
    return highest + 1


def get_or_create_roles_and_shifts(db):
    roles = db.query(EmployeeRole).order_by(EmployeeRole.id).all()
    if not roles:
        roles = [
            EmployeeRole(role_code="MANAGER", role_name="Store Manager"),
            EmployeeRole(role_code="CASHIER", role_name="Cashier"),
            EmployeeRole(role_code="STOCK", role_name="Stock Associate"),
            EmployeeRole(role_code="AUDITOR", role_name="Inventory Auditor"),
        ]
        db.add_all(roles)
        db.flush()

    shifts = db.query(Shift).order_by(Shift.id).all()
    if not shifts:
        shifts = [
            Shift(
                shift_code="MORNING", shift_name="Morning Shift",
                start_time=time(6, 0), end_time=time(14, 0),
            ),
            Shift(
                shift_code="EVENING", shift_name="Evening Shift",
                start_time=time(14, 0), end_time=time(22, 0),
            ),
        ]
        db.add_all(shifts)
        db.flush()

    if len(roles) < 4 or len(shifts) < 1:
        raise RuntimeError(
            "Expected at least 4 employee roles and 1 shift in the database."
        )
    return roles, shifts


def add_missing_master_data(db, rng, target_stores, target_skus):
    existing_stores = db.query(Store).order_by(Store.id).all()
    existing_skus = db.query(SKU).order_by(SKU.id).all()

    if len(existing_stores) > target_stores or len(existing_skus) > target_skus:
        raise RuntimeError(
            "Existing master-data count exceeds requested target. "
            "No data was changed."
        )

    next_store = next_code_number(db, Store, Store.store_code)
    next_sku = next_code_number(db, SKU, SKU.sku_code)

    new_stores = []
    for number in range(next_store, next_store + target_stores - len(existing_stores)):
        new_stores.append(
            Store(
                store_code=f"STORE-{number:06d}",
                name=f"Retail Store {number}",
                city=rng.choice(["Indore", "Bhopal", "Jaipur", "Delhi"]),
                state="India",
                is_active=True,
            )
        )

    new_skus = []
    for number in range(next_sku, next_sku + target_skus - len(existing_skus)):
        cost = Decimal(str(round(rng.uniform(10, 1000), 2)))
        new_skus.append(
            SKU(
                sku_code=f"SKU-{number:06d}",
                name=f"Product {number}",
                category=rng.choice(CATEGORIES),
                unit_cost=cost,
                unit_price=(cost * Decimal("1.30")).quantize(Decimal("0.01")),
                is_active=True,
            )
        )

    db.add_all(new_stores + new_skus)
    db.flush()

    stores = db.query(Store).order_by(Store.id).all()
    skus = db.query(SKU).order_by(SKU.id).all()
    roles, shifts = get_or_create_roles_and_shifts(db)

    return stores, skus, roles, shifts, existing_stores, existing_skus


def latest_movement_time(db):
    return db.query(func.max(InventoryMovement.effective_at)).scalar() or BASE_DATE


def get_current_balances(db):
    """Rebuild current stock from all movements already in the database."""
    balances = {}
    rows = (
        db.query(
            InventoryMovement.store_id,
            InventoryMovement.sku_id,
            InventoryMovement.movement_type,
            func.sum(InventoryMovement.quantity),
        )
        .group_by(
            InventoryMovement.store_id,
            InventoryMovement.sku_id,
            InventoryMovement.movement_type,
        )
        .all()
    )

    positive = {
        "OPENING_BALANCE", "RECEIPT", "RETURN_IN",
        "TRANSFER_IN", "ADJUSTMENT_IN",
    }
    negative = {
        "SALE", "DAMAGE", "TRANSFER_OUT", "ADJUSTMENT_OUT",
    }

    for store_id, sku_id, movement_type, quantity in rows:
        key = (store_id, sku_id)
        balances.setdefault(key, Decimal("0"))
        if movement_type in positive:
            balances[key] += Decimal(quantity or 0)
        elif movement_type in negative:
            balances[key] -= Decimal(quantity or 0)

    return balances


def generate_additional_movements(
    db, rng, stores, skus, roles, shifts,
    target_total_movements, existing_store_ids, existing_sku_ids,
):
    existing_count = db.query(InventoryMovement).count()
    if existing_count > target_total_movements:
        raise RuntimeError("Existing movement count exceeds requested target.")

    balances = get_current_balances(db)
    current_time = latest_movement_time(db) + timedelta(days=2)

    movement_number = next_code_number(
        db, InventoryMovement, InventoryMovement.movement_code
    )
    transfer_number = 1
    existing_transfer_ids = (
        db.query(InventoryMovement.transfer_group_id)
        .filter(InventoryMovement.transfer_group_id.isnot(None))
        .all()
    )
    for (transfer_id,) in existing_transfer_ids:
        try:
            transfer_number = max(
                transfer_number, int(transfer_id.rsplit("-", 1)[-1]) + 1
            )
        except (ValueError, AttributeError):
            pass

    batch = []
    created = 0

    def add_movement(
        store_id, sku_id, movement_type, quantity,
        role_id, shift_id, transfer_group_id=None,
    ):
        nonlocal movement_number, created, batch
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
        movement_number += 1
        created += 1

        if len(batch) >= 1000:
            db.add_all(batch)
            db.flush()
            batch = []

    # Add opening stock only for store/SKU combinations that did not exist
    # in the original Starter dataset.
    new_combinations = []
    for store in stores:
        for sku in skus:
            key = (store.id, sku.id)
            if key not in balances:
                opening = rng.randint(40, 150)
                balances[key] = Decimal(opening)
                new_combinations.append((store, sku, opening))

    remaining = target_total_movements - existing_count
    if len(new_combinations) > remaining:
        raise RuntimeError(
            "Not enough movement slots for opening balances of new "
            "store-SKU combinations. No data was committed."
        )

    print(
        f"Adding {len(new_combinations):,} opening balances for new "
        "store-SKU combinations..."
    )
    for store, sku, opening in new_combinations:
        add_movement(
            store.id, sku.id, "OPENING_BALANCE",
            opening, roles[0].id, shifts[0].id,
        )

    remaining -= len(new_combinations)
    print(f"Adding {remaining:,} operational movements...")

    while remaining > 0:
        current_time += timedelta(minutes=rng.randint(1, 60))
        store = rng.choice(stores)
        sku = rng.choice(skus)
        key = (store.id, sku.id)
        stock = int(balances[key])

        role = rng.choice(roles)
        shift = rng.choice(shifts)
        operation = rng.choices(
            ["SALE", "RECEIPT", "DAMAGE", "TRANSFER"],
            weights=[55, 25, 10, 10],
        )[0]

        quantity = rng.randint(1, min(10, max(stock, 1)))

        if operation == "SALE" and stock >= quantity:
            add_movement(
                store.id, sku.id, "SALE", quantity, role.id, shift.id
            )
            balances[key] -= quantity
            remaining -= 1

        elif operation == "DAMAGE" and stock >= quantity:
            add_movement(
                store.id, sku.id, "DAMAGE", quantity, role.id, shift.id
            )
            balances[key] -= quantity
            remaining -= 1

        elif (
            operation == "TRANSFER"
            and stock >= quantity
            and remaining >= 2
            and len(stores) > 1
        ):
            destination = rng.choice(
                [candidate for candidate in stores if candidate.id != store.id]
            )
            transfer_id = f"TRF-{transfer_number:08d}"
            transfer_number += 1

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
            remaining -= 2

        else:
            quantity = rng.randint(5, 25)
            add_movement(
                store.id, sku.id, "RECEIPT", quantity, role.id, shift.id
            )
            balances[key] += quantity
            remaining -= 1

    if batch:
        db.add_all(batch)
        db.flush()

    print(f"Added {created:,} movements.")
    return balances, current_time


def append_ground_truth(rows):
    output_file = OUTPUT_DIR / "ground_truth.csv"
    fieldnames = [
        "count_code", "store_code", "sku_code",
        "expected_quantity", "observed_quantity",
        "missing_quantity", "is_shrinkage",
    ]

    file_exists = output_file.exists() and output_file.stat().st_size > 0
    with output_file.open("a" if file_exists else "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    print(f"Ground truth appended: {output_file}")


def generate_additional_cycle_counts(
    db, rng, stores, skus, roles, shifts,
    balances, target_total_counts, movement_end_time,
):
    existing_count = db.query(CycleCount).count()
    if existing_count > target_total_counts:
        raise RuntimeError("Existing cycle count exceeds requested target.")

    remaining = target_total_counts - existing_count
    if remaining == 0:
        print("Cycle count target already reached.")
        return

    existing_pairs = set(
        db.query(CycleCount.store_id, CycleCount.sku_id).all()
    )
    available = [
        (store, sku)
        for store in stores
        for sku in skus
        if (store.id, sku.id) not in existing_pairs
    ]

    if remaining > len(available):
        raise RuntimeError("Not enough uncounted store-SKU pairs.")

    rng.shuffle(available)
    selected = available[:remaining]

    count_number = next_code_number(
        db, CycleCount, CycleCount.count_code
    )
    counted_at = movement_end_time + timedelta(days=1)

    batch = []
    ground_truth_rows = []
    created_shrinkage = 0

    for store, sku in selected:
        expected = int(balances[(store.id, sku.id)])
        is_shrinkage = rng.random() < 0.10

        missing = (
            rng.randint(5, min(20, expected))
            if is_shrinkage and expected >= 5
            else 0
        )
        observed = expected - missing
        count_code = f"CNT-2026-{count_number:06d}"
        count_number += 1

        batch.append(
            CycleCount(
                count_code=count_code,
                store_id=store.id,
                sku_id=sku.id,
                employee_role_id=roles[3].id,
                shift_id=shifts[0].id,
                counted_quantity=Decimal(str(observed)),
                counted_at=counted_at,
                recorded_at=counted_at + timedelta(minutes=5),
                count_status="COMPLETED",
            )
        )

        ground_truth_rows.append({
            "count_code": count_code,
            "store_code": store.store_code,
            "sku_code": sku.sku_code,
            "expected_quantity": expected,
            "observed_quantity": observed,
            "missing_quantity": missing,
            "is_shrinkage": int(missing > 0),
        })
        created_shrinkage += int(missing > 0)

        if len(batch) >= 500:
            db.add_all(batch)
            db.flush()
            batch = []

    if batch:
        db.add_all(batch)
        db.flush()

    append_ground_truth(ground_truth_rows)
    print(f"Added {remaining:,} cycle counts.")
    print(f"New injected shrinkage cases: {created_shrinkage:,}")


def main():
    parser = argparse.ArgumentParser(
        description="Append synthetic inventory data up to target totals."
    )
    parser.add_argument(
        "--append-full",
        action="store_true",
        help="Append data until full target totals are reached; preserves existing data.",
    )
    args = parser.parse_args()

    if not args.append_full:
        parser.error("Use --append-full. This script is designed to preserve existing data.")

    rng = random.Random(SEED)
    target_stores = 100
    target_skus = 5000
    target_movements = 1_000_000
    target_counts = 20_000

    db = SessionLocal()
    try:
        print("Starting incremental FULL dataset generation...")
        print("Existing records will be preserved.")

        stores, skus, roles, shifts, old_stores, old_skus = (
            add_missing_master_data(
                db, rng, target_stores, target_skus
            )
        )

        print(
            f"Stores: {len(old_stores)} existing, "
            f"{len(stores) - len(old_stores)} added."
        )
        print(
            f"SKUs: {len(old_skus)} existing, "
            f"{len(skus) - len(old_skus)} added."
        )

        existing_store_ids = {store.id for store in old_stores}
        existing_sku_ids = {sku.id for sku in old_skus}

        balances, movement_end_time = generate_additional_movements(
            db, rng, stores, skus, roles, shifts,
            target_movements, existing_store_ids, existing_sku_ids,
        )

        generate_additional_cycle_counts(
            db, rng, stores, skus, roles, shifts,
            balances, target_counts, movement_end_time,
        )

        db.commit()

        print("\nINCREMENTAL DATA GENERATION COMPLETED")
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
