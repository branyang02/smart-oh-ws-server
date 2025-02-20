import json
import logging
import os
from http.cookies import SimpleCookie

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from src.db.db import get_role_by_user_id_class_id, get_user_by_session_token
from src.websocket.state import TBoard, TCard
from src.websocket.websocket_manager import OfficeHourManager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ENV = os.getenv("ENV", "dev")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ENV == "prod" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = OfficeHourManager()


@app.get("/")
async def home_endpoint():
    return {"message": "WebSocket server is running and ready to connect!"}


async def authenticate_websocket(websocket: WebSocket, class_id: str):
    """
    Authenticate the websocket connection using cookies.
    If authentication fails, close the connection and raise an HTTPException.
    """
    cookie_header = websocket.headers.get("cookie")
    if not cookie_header:
        logger.warning("Missing cookie header")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION, detail="Missing cookie header"
        )

    cookies = SimpleCookie()
    cookies.load(cookie_header)

    session_cookie = cookies.get("authjs.session-token")
    if not session_cookie:
        logger.warning("Missing session token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION, detail="Missing session token"
        )

    session_token = session_cookie.value

    # Query the database for user authentication
    user = get_user_by_session_token(session_token)
    if not user:
        logger.warning("Invalid session token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.WS_1008_POLICY_VIOLATION, detail="Invalid session token"
        )

    role = get_role_by_user_id_class_id(user.id, class_id)
    return user, role


@app.websocket("/ws/{class_id}")
async def websocket_endpoint(websocket: WebSocket, class_id: str):
    try:
        user, role = await authenticate_websocket(websocket, class_id)
        await websocket.accept()
        manager.add_connection(class_id, websocket)

        # Get or create the board for this class and add the user if not already present
        board = manager.get_or_create_room(class_id)
        if not any(c.user.id == user.id for c in board.allUsers):
            board.allUsers.append(TCard(user=user, role=role))

        await websocket.send_text(board.model_dump_json())

        while True:
            try:
                msg = await websocket.receive_text()
                new_state = TBoard.model_validate_json(msg)
                manager.rooms[class_id] = new_state
                await manager.broadcast(class_id, new_state.model_dump_json())
            except Exception as e:
                error_message = {"error": str(e)}
                logger.error(f"Error processing message: {error_message}")
                await websocket.send_text(json.dumps(error_message))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for class {class_id}")
    finally:
        manager.remove_connection(class_id, websocket)
