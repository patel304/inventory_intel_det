from decimal import Decimal


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_expected_stock_and_variance_endpoints(client, seeded):
    store_id = seeded["store_a"].id
    sku_id = seeded["sku"].id
    as_of = "2026-01-01T08:00:00"
    response = client.get(f"/inventory/expected-stock/{store_id}/{sku_id}", params={"as_of": as_of})
    assert response.status_code == 200
    assert response.json()["expected_stock"] == "100"

    missing = client.get("/inventory/expected-stock/999/999")
    assert missing.status_code == 404

    variance = client.post(
        "/inventory/variance",
        json={"store_id": store_id, "sku_id": sku_id, "counted_quantity": "40", "as_of": as_of},
    )
    assert variance.status_code == 200
    assert variance.json()["variance_type"] == "SHORTAGE"


def test_alert_and_investigation_api_flow(client, seeded):
    store_id = seeded["store_a"].id
    sku_id = seeded["sku"].id
    detect = client.post(
        "/alerts/detect",
        json={
            "store_id": store_id,
            "sku_id": sku_id,
            "counted_quantity": "40",
            "as_of": "2026-01-01T08:00:00",
        },
    )
    assert detect.status_code == 200
    body = detect.json()
    assert body["alert_created"] is True
    alert_id = body["alert_id"]

    listed = client.get("/alerts")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["variance"] is not None

    detail = client.get(f"/alerts/{alert_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == alert_id

    created = client.post("/investigations", json={"alert_id": alert_id, "assigned_to": "Ada"})
    assert created.status_code == 200
    investigation_id = created.json()["investigation_id"]

    duplicate = client.post("/investigations", json={"alert_id": alert_id})
    assert duplicate.status_code == 409

    invalid = client.put(
        f"/investigations/{investigation_id}",
        json={"findings": "x", "resolution": "y", "status": "NOPE"},
    )
    assert invalid.status_code == 400

    updated = client.put(
        f"/investigations/{investigation_id}",
        json={
            "findings": "Reviewed CCTV",
            "resolution": "Process change",
            "status": "RESOLVED",
            "performed_by": "Ada",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "RESOLVED"

    events = client.get(f"/investigations/{investigation_id}/events")
    assert events.status_code == 200
    assert len(events.json()["events"]) == 2

    dashboard = client.get("/dashboard/summary")
    assert dashboard.status_code == 200
    assert dashboard.json()["stores"] == 2
    assert dashboard.json()["alerts_total"] == 1


def test_validation_error(client, seeded):
    response = client.post(
        "/inventory/variance",
        json={"store_id": seeded["store_a"].id, "sku_id": seeded["sku"].id, "counted_quantity": "-1"},
    )
    assert response.status_code == 422
