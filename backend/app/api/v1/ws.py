"""WebSocket endpoint streaming live system telemetry to the dashboard.

This replaces the frontend's local setInterval simulation once connected --
the frontend is wired to consume this in a later frontend iteration; for now
it emits real, server-generated heartbeat/status payloads on a fixed cadence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("zeroday.ws")

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        stale: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:  # connection already gone
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


@router.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            payload = {
                "type": "system.status",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ai_status": "ONLINE",
                "active_connections": manager.active_count,
            }
            await websocket.send_json(payload)

            try:
                # Allow the client to send control messages (e.g. ping) without
                # blocking the heartbeat cadence.
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=5)
                if raw:
                    logger.debug("dashboard ws received: %s", raw)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
