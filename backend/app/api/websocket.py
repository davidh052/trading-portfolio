from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for real-time stock updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: dict = {}  # {websocket: [symbols]}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        """Subscribe to stock price updates"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket] = symbols

    async def broadcast_price_update(self, symbol: str, data: dict):
        """Send price update to all subscribers of a symbol"""
        for websocket, symbols in self.subscriptions.items():
            if symbol in symbols:
                await websocket.send_json({
                    "type": "price_update",
                    "symbol": symbol,
                    "data": data
                })

manager = ConnectionManager()

@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time stock price updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                symbols = message.get("symbols", [])
                await manager.subscribe(websocket, symbols)
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })

            # TODO: Implement fetching real-time prices and broadcasting

    except WebSocketDisconnect:
        manager.disconnect(websocket)
