"""
Tests for the task endpoints.
"""
import pytest

NEW_TASK = {"title": "Review stock", "priority": "high", "dueDate": "2025-10-08"}


class TestTaskEndpoints:
    """Test suite for /api/tasks."""

    def test_get_tasks_starts_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        response = client.post("/api/tasks", json=NEW_TASK)
        assert response.status_code == 201

        task = response.json()
        assert task["id"] == "task-1"
        assert task["status"] == "pending"
        assert task["title"] == NEW_TASK["title"]
        assert task["dueDate"] == NEW_TASK["dueDate"]
        assert client.get("/api/tasks").json() == [task]

    def test_create_task_requires_title_and_due_date(self, client):
        response = client.post("/api/tasks", json={"title": "No date"})
        assert response.status_code == 422

    def test_toggle_task_flips_status(self, client):
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]

        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_task(self, client):
        task_id = client.post("/api/tasks", json=NEW_TASK).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_ids_not_reused_after_delete(self, client):
        first = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        client.delete(f"/api/tasks/{first}")
        second = client.post("/api/tasks", json=NEW_TASK).json()["id"]
        assert second != first

    def test_unknown_task_returns_404(self, client):
        assert client.patch("/api/tasks/nope").status_code == 404
        assert client.delete("/api/tasks/nope").status_code == 404
