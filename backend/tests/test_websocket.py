from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_websocket_streams_status() -> None:
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/dashboard") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "system.status"
        assert message["ai_status"] == "ONLINE"
        assert "timestamp" in message
