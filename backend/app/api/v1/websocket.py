"""
WebSocket API Router
Handles real-time streaming updates for active test runs and agent pipeline stages.
"""
from __future__ import annotations

import asyncio
import json
from typing import Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections grouped by project/pipeline."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    def _norm(self, channel_id: str) -> str:
        return str(channel_id).replace("-", "").lower()

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        key = self._norm(channel_id)
        if key not in self.active_connections:
            self.active_connections[key] = set()
        self.active_connections[key].add(websocket)
        logger.info(f"🔌 Client connected to channel {channel_id} (norm: {key})")

    def disconnect(self, websocket: WebSocket, channel_id: str):
        key = self._norm(channel_id)
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)
            if not self.active_connections[key]:
                del self.active_connections[key]
        logger.info(f"🔌 Client disconnected from channel {channel_id}")

    async def broadcast(self, channel_id: str, message: dict):
        """Send message to all clients in this channel safely."""
        key = self._norm(channel_id)
        if key in self.active_connections:
            data = json.dumps(message)
            conns = list(self.active_connections[key])
            stale_conns = []
            for connection in conns:
                try:
                    await connection.send_text(data)
                except Exception:
                    stale_conns.append(connection)

            for stale in stale_conns:
                self.active_connections[key].discard(stale)


manager = ConnectionManager()


@router.websocket("/ws/{channel_id}")
@router.websocket("/ws/runs/{channel_id}")
@router.websocket("/ws/projects/{channel_id}")
async def websocket_endpoint(websocket: WebSocket, channel_id: str):
    """
    WebSocket endpoint for real-time live execution updates.
    channel_id can be a project_id or run_id.
    """
    await manager.connect(websocket, channel_id)
    try:
        # Send initial connected greeting
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "channel_id": channel_id,
                "message": "Connected to real-time AI Agent execution stream",
            })
        )
        while True:
            # Keep alive and listen for client messages / pings
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel_id)


async def send_pipeline_event(channel_id: str, event_type: str, payload: dict):
    """Utility to broadcast an agent event from orchestrator to frontend."""
    message = {
        "type": event_type,
        "data": payload,
        "payload": payload,
        "runId": payload.get("run_id") or channel_id,
        "projectId": payload.get("project_id") or channel_id,
        "channel_id": channel_id,
    }
    await manager.broadcast(channel_id, message)

