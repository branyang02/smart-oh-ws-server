import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


from websocket_manager import OfficeHourManager, TBoard
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = OfficeHourManager()


@app.websocket("/ws/{class_id}")
async def websocket_endpoint(websocket: WebSocket, class_id: str):
    await websocket.accept()

    manager.add_connection(class_id, websocket)

    board = manager.get_or_create_room(class_id)
    await websocket.send_text(board.model_dump_json())

    try:
        while True:
            msg = await websocket.receive_text()

            try:
                new_state = TBoard.model_validate_json(msg)
                manager.rooms[class_id] = new_state
                await manager.broadcast(class_id, new_state.json())

            except Exception as e:
                error_message = {"error": str(e)}
                print(f"Error: {error_message}")
                await websocket.send_text(json.dumps(error_message))

    except WebSocketDisconnect:
        # Client disconnected, remove from manager
        manager.remove_connection(class_id, websocket)
