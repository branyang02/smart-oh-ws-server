import asyncio
import time
import websockets
import json
from urllib.parse import urlencode


async def connect_user(
    user_id: str, name: str, user_type: str, class_id: str = "cs101"
):
    """Helper function to connect a user to the websocket"""
    params = urlencode({"user_type": user_type, "name": name})
    uri = f"ws://localhost:8000/ws/{class_id}/{user_id}?{params}"
    return await websockets.connect(uri)


async def receive_messages(ws):
    """Helper function to receive messages from the websocket"""
    while True:
        try:
            message = await ws.recv()
            print(f"Received message: {message}")
        except websockets.ConnectionClosed:
            break


async def basic_test():
    print("Starting basic test...")

    # Connect a TA
    ta1_ws = await connect_user("ta1", "John TA", "TA")
    print("ta1 connected")
    ta2_ws = await connect_user("ta2", "Jane TA", "TA")
    print("ta2 connected")
    student1_ws = await connect_user("student1", "Alice Student", "student")
    print("student1 connected")
    student2_ws = await connect_user("student2", "Bob Student", "student")
    print("student2 connected")
    student3_ws = await connect_user("student3", "Charlie Student", "student")
    print("student3 connected")

    # Student 1 joins the queue
    await student1_ws.send(json.dumps({"action": "join_queue"}))
    print("student1 joined the queue")
    time.sleep(0.03)
    # Student 2 joins the queue
    await student2_ws.send(json.dumps({"action": "join_queue"}))
    print("student2 joined the queue")
    time.sleep(0.03)
    # Student 3 joins the queue
    await student3_ws.send(json.dumps({"action": "join_queue"}))
    print("student3 joined the queue")
    time.sleep(0.03)
    # Student 2 leaves the queue
    await student2_ws.send(json.dumps({"action": "leave_queue"}))
    print("student2 left the queue")
    time.sleep(0.03)
    # Student 1 leaves the queue
    await student1_ws.send(json.dumps({"action": "leave_queue"}))
    print("student1 left the queue")
    time.sleep(0.03)
    # ta1 creates a session
    await ta1_ws.send(
        json.dumps({"action": "create_session_with_id", "new_session_id": "session-1"})
    )
    print("ta1 created a session")
    time.sleep(0.03)
    # ta2 creates a session
    await ta2_ws.send(
        json.dumps({"action": "create_session_with_id", "new_session_id": "session-2"})
    )
    print("ta2 created a session")
    time.sleep(0.03)
    # ta2 drags student3 to session-2
    await ta2_ws.send(
        json.dumps(
            {
                "action": "assign_student_to_session",
                "student_id": "student3",
                "session_id": "session-2",
            }
        )
    )
    print("ta2 assigned student3 to the session")
    time.sleep(0.03)
    # student 1 joins the queue
    await student1_ws.send(json.dumps({"action": "join_queue"}))
    print("student1 joined the queue")
    time.sleep(0.03)
    # student 4 joins the queue
    student4_ws = await connect_user("student4", "David Student", "student")
    print("student4 connected")
    await student4_ws.send(json.dumps({"action": "join_queue"}))
    print("student4 joined the queue")
    time.sleep(0.03)
    print("ta1 assigned student1 to the session")
    # student5 joins the queue
    student5_ws = await connect_user("student5", "Eve Student", "student")
    print("student5 connected")
    await student5_ws.send(json.dumps({"action": "join_queue"}))
    print("student5 joined the queue")
    time.sleep(0.03)
    # student6 joins the queue
    student6_ws = await connect_user("student6", "Frank Student", "student")
    print("student6 connected")
    await student6_ws.send(json.dumps({"action": "join_queue"}))
    print("student6 joined the queue")
    time.sleep(0.03)
    # student7 joins the queue
    student7_ws = await connect_user("student7", "Grace Student", "student")
    print("student7 connected")
    await student7_ws.send(json.dumps({"action": "join_queue"}))
    print("student7 joined the queue")
    time.sleep(0.03)
    # ta1 drags student1 to session-1
    await ta1_ws.send(
        json.dumps(
            {
                "action": "assign_student_to_session",
                "student_id": "student1",
                "session_id": "session-1",
            }
        )
    )
    print("ta1 assigned student1 to the session")
    time.sleep(0.03)
    # ta1 drags student4 to session-1
    await ta1_ws.send(
        json.dumps(
            {
                "action": "assign_student_to_session",
                "student_id": "student4",
                "session_id": "session-1",
            }
        )
    )
    print("ta1 assigned student4 to the session")
    time.sleep(0.03)
    # student8 joins the queue
    student8_ws = await connect_user("student8", "Hank Student", "student")
    print("student8 connected")
    await student8_ws.send(json.dumps({"action": "join_queue"}))
    print("student8 joined the queue")
    time.sleep(0.03)
    # student9 joins the queue
    student9_ws = await connect_user("student9", "Ivy Student", "student")
    print("student9 connected")
    await student9_ws.send(json.dumps({"action": "join_queue"}))
    print("student9 joined the queue")
    time.sleep(0.03)
    # TA3 creates a session
    ta3_ws = await connect_user("ta3", "Kate TA", "TA")
    print("ta3 connected")
    await ta3_ws.send(
        json.dumps({"action": "create_session_with_id", "new_session_id": "session-3"})
    )
    print("ta3 created a session")
    time.sleep(0.03)

    await receive_messages(ta1_ws)
    return
    time.sleep(0.03)
    # student 1 accidently disconnects
    student1_ws.close()
    print("student1 disconnected")
    time.sleep(0.03)
    # student 1 reconnects
    student1_ws = await connect_user("student1", "Alice Student", "student")
    print("student1 reconnected")
    time.sleep(0.03)
    # ta1 drags student1 to session-1
    await ta1_ws.send(
        json.dumps(
            {
                "action": "assign_student_to_session",
                "student_id": "student1",
                "session_id": "session-1",
            }
        )
    )
    # ta2 reassigns student3 to session-1
    await ta2_ws.send(
        json.dumps(
            {
                "action": "assign_student_to_session",
                "student_id": "student3",
                "session_id": "session-1",
            }
        )
    )
    print("ta2 reassigned student3 to the session")
    time.sleep(0.03)
    # ta2 leaves the session
    await ta2_ws.send(json.dumps({"action": "leave_session"}))
    print("ta2 left the session")
    time.sleep(0.03)
    # ta1 creates session-2
    await ta1_ws.send(
        json.dumps({"action": "create_session_with_id", "new_session_id": "session-3"})
    )
    print("ta1 created a session")
    time.sleep(0.03)
    # ta1 drags student1 to session-3
    await ta1_ws.send(
        json.dumps(
            {
                "action": "assign_student_to_session",
                "student_id": "student1",
                "session_id": "session-3",
            }
        )
    )
    # student 2 leaves completely
    student2_ws.close()
    print("student2 disconnected")
    time.sleep(0.03)
    # student 3 leaves completely
    student3_ws.close()
    print("student3 disconnected")
    time.sleep(0.03)
    # ta2 joins ta1's session
    await ta2_ws.send(
        json.dumps({"action": "join_session", "new_session_id": "session-3"})
    )
    print("ta2 joined ta1's session")
    time.sleep(0.03)
    # ta2 puts student1 in the queue
    await ta2_ws.send(
        json.dumps({"action": "add_student_to_queue", "student_id": "student1"})
    )
    print("ta2 put student1 in the queue")


if __name__ == "__main__":
    asyncio.run(basic_test())
