from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import CycleCount, InventoryMovement, SKU, Store


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, _connection_record):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(db):
    store_a = Store(store_code="STORE-1", name="Store A", city="Indore", state="MP", is_active=True)
    store_b = Store(store_code="STORE-2", name="Store B", city="Bhopal", state="MP", is_active=True)
    sku = SKU(
        sku_code="SKU-1",
        name="Milk",
        category="Dairy",
        unit_cost=10,
        unit_price=13,
        is_active=True,
    )
    db.add_all([store_a, store_b, sku])
    db.flush()

    t0 = datetime(2026, 1, 1, 8, 0, 0)
    movements = [
        InventoryMovement(
            movement_code="MOV-1",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="OPENING_BALANCE",
            quantity=100,
            effective_at=t0,
            recorded_at=t0,
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-2",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="RECEIPT",
            quantity=20,
            effective_at=t0 + timedelta(days=1),
            recorded_at=t0 + timedelta(days=1),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-3",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="SALE",
            quantity=15,
            effective_at=t0 + timedelta(days=2),
            recorded_at=t0 + timedelta(days=2),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-4",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="DAMAGE",
            quantity=5,
            effective_at=t0 + timedelta(days=3),
            recorded_at=t0 + timedelta(days=3),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-5",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="TRANSFER_OUT",
            quantity=10,
            transfer_group_id="TRF-1",
            effective_at=t0 + timedelta(days=4),
            recorded_at=t0 + timedelta(days=4),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-6",
            store_id=store_b.id,
            sku_id=sku.id,
            movement_type="TRANSFER_IN",
            quantity=10,
            transfer_group_id="TRF-1",
            effective_at=t0 + timedelta(days=4),
            recorded_at=t0 + timedelta(days=4),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-7",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="RETURN_IN",
            quantity=4,
            effective_at=t0 + timedelta(days=5),
            recorded_at=t0 + timedelta(days=5),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-8",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="ADJUSTMENT_IN",
            quantity=3,
            effective_at=t0 + timedelta(days=6),
            recorded_at=t0 + timedelta(days=6),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-9",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="ADJUSTMENT_OUT",
            quantity=2,
            effective_at=t0 + timedelta(days=7),
            recorded_at=t0 + timedelta(days=7),
            source_system="TEST",
        ),
        InventoryMovement(
            movement_code="MOV-10",
            store_id=store_a.id,
            sku_id=sku.id,
            movement_type="SALE",
            quantity=50,
            effective_at=t0 + timedelta(days=20),
            recorded_at=t0 + timedelta(days=20),
            source_system="TEST",
        ),
    ]
    db.add_all(movements)
    count = CycleCount(
        count_code="CNT-1",
        store_id=store_a.id,
        sku_id=sku.id,
        counted_quantity=95,
        counted_at=t0 + timedelta(days=7, hours=12),
        recorded_at=t0 + timedelta(days=7, hours=12),
        count_status="COMPLETED",
    )
    db.add(count)
    db.flush()
    return {"store_a": store_a, "store_b": store_b, "sku": sku, "count": count, "t0": t0}
