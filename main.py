import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from http.cookies import SimpleCookie


from db import get_user_by_session_token
from state import TCard
from websocket_manager import OfficeHourManager, TBoard
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

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
    cookie_header = websocket.headers.get("cookie")
    if not cookie_header:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    cookies = SimpleCookie()
    cookies.load(cookie_header)

    session_cookie = cookies.get("authjs.session-token")
    if not session_cookie:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    session_token = session_cookie.value

    # Query the DB
    user = get_user_by_session_token(session_token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    role = websocket.query_params.get("role", "student")

    await websocket.accept()
    manager.add_connection(class_id, websocket)

    # Add user to the board if not already present
    board = manager.get_or_create_room(class_id)
    for c in board.allUsers:
        if c.user.id == user.id:
            break
    else:
        board.allUsers.append(TCard(user=user, role=role))

    await websocket.send_text(board.model_dump_json())

    try:
        while True:
            msg = await websocket.receive_text()

            try:
                new_state = TBoard.model_validate_json(msg)
                manager.rooms[class_id] = new_state
                await manager.broadcast(class_id, new_state.model_dump_json())

            except Exception as e:
                error_message = {"error": str(e)}
                print(f"Error: {error_message}")
                await websocket.send_text(json.dumps(error_message))

    except WebSocketDisconnect:
        # Client disconnected, remove from manager
        manager.remove_connection(class_id, websocket)
