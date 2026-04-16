from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, scan_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[scan_id].add(websocket)

    def disconnect(self, scan_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(scan_id)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self._connections.pop(scan_id, None)

    async def notify(self, scan_id: str, payload: dict) -> None:
        for websocket in list(self._connections.get(scan_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(scan_id, websocket)

    async def close_all(self) -> None:
        for scan_id, conns in list(self._connections.items()):
            for websocket in list(conns):
                try:
                    await websocket.close()
                except Exception:
                    pass
                self.disconnect(scan_id, websocket)


manager = ConnectionManager()


async def notify_client(scan_id: str, payload: dict) -> None:
    await manager.notify(scan_id, payload)


@router.websocket("/{scan_id}")
async def scan_updates(websocket: WebSocket, scan_id: str) -> None:
    await manager.connect(scan_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(scan_id, websocket)
