from fastapi import WebSocket
from typing import Dict, List

from pydantic import BaseModel


# Match Frontend
class TCard(BaseModel):
    id: str
    name: str
    type: str


class TColumn(BaseModel):
    id: str
    title: str
    cards: List[TCard]


class TBoard(BaseModel):
    classId: str
    allUsers: List[TCard]
    columns: List[TColumn]


class OfficeHourManager:
    def __init__(self):
        # class_id -> TBoard
        self.rooms: Dict[str, TBoard] = {}

        # class_id -> list of active WebSocket connections
        self.connections: Dict[str, List[WebSocket]] = {}

    def get_or_create_room(self, class_id: str) -> TBoard:
        if class_id not in self.rooms:
            self.rooms[class_id] = TBoard(classId=class_id, allUsers=[], columns=[])
        return self.rooms[class_id]

    def add_connection(self, class_id: str, websocket: WebSocket) -> None:
        if class_id not in self.connections:
            self.connections[class_id] = []
        self.connections[class_id].append(websocket)

    def remove_connection(self, class_id: str, websocket: WebSocket) -> None:
        if class_id in self.connections:
            self.connections[class_id].remove(websocket)
            if not self.connections[class_id]:
                del self.connections[class_id]

    async def broadcast(self, class_id: str, data: str) -> None:
        """Send `data` to all clients connected to a particular class."""
        if class_id in self.connections:
            for connection in self.connections[class_id]:
                await connection.send_text(data)
