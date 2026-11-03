"""
Tests for the purchase order endpoints.
"""
import pytest


def po_request(backlog_item_id):
    return {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 100,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-15",
        "notes": "Rush",
    }


@pytest.fixture
def backlog_item_id(client):
    return client.get("/api/backlog").json()[0]["id"]


class TestPurchaseOrderEndpoints:
    """Test suite for /api/purchase-orders."""

    def test_create_purchase_order(self, client, backlog_item_id):
        response = client.post("/api/purchase-orders", json=po_request(backlog_item_id))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["status"] == "Pending"
        assert po["backlog_item_id"] == backlog_item_id
        assert po["supplier_name"] == "Acme Supply"
        assert po["created_date"]

    def test_created_po_marks_backlog_item(self, client, backlog_item_id):
        client.post("/api/purchase-orders", json=po_request(backlog_item_id))

        item = next(i for i in client.get("/api/backlog").json() if i["id"] == backlog_item_id)
        assert item["has_purchase_order"] is True

    def test_create_for_unknown_backlog_item_returns_404(self, client):
        response = client.post("/api/purchase-orders", json=po_request("does-not-exist"))
        assert response.status_code == 404

    def test_duplicate_purchase_order_returns_400(self, client, backlog_item_id):
        client.post("/api/purchase-orders", json=po_request(backlog_item_id))
        response = client.post("/api/purchase-orders", json=po_request(backlog_item_id))
        assert response.status_code == 400

    def test_get_purchase_order_by_backlog_item(self, client, backlog_item_id):
        created = client.post("/api/purchase-orders", json=po_request(backlog_item_id)).json()

        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_missing_purchase_order_returns_404(self, client, backlog_item_id):
        assert client.get(f"/api/purchase-orders/{backlog_item_id}").status_code == 404
