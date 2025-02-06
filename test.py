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


async def basic_test():
    print("Starting basic test...")

    # Connect a TA
    ta_ws = await connect_user("ta1", "John TA", "TA")
    print("TA connected")

    # Connect two students
    student1_ws = await connect_user("student1", "Alice", "student")
    student2_ws = await connect_user("student2", "Bob", "student")
    print("Students connected")

    # Have students join queue
    await student1_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 1 joined queue")
    time.sleep(0.05)

    await student2_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 2 joined queue")
    time.sleep(0.05)

    # Have TA create a session
    await ta_ws.send(json.dumps({"action": "join_session"}))
    print("TA created session")
    time.sleep(0.05)

    # TA assigns first student
    await ta_ws.send(
        json.dumps({"action": "assign_student_to_session", "student_id": "student1"})
    )
    print("TA assigned student 1")
    time.sleep(0.05)

    # TA assigns second student
    await ta_ws.send(
        json.dumps({"action": "assign_student_to_session", "student_id": "student2"})
    )
    print("TA assigned student 2")
    time.sleep(0.05)

    # Another TA joins
    ta2_ws = await connect_user("ta2", "Jane TA", "TA")
    print("TA 2 connected")
    time.sleep(0.05)

    # TA 2 joins TA 1's session
    await ta2_ws.send(json.dumps({"action": "join_session", "session_id": "ta1"}))
    print("TA 2 joined TA 1's session")
    time.sleep(0.05)

    # Student 3 joins
    student3_ws = await connect_user("student3", "Charlie", "student")
    print("Student 3 connected")
    time.sleep(0.05)

    # student 3 joins the queue
    await student3_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 3 joined queue")
    time.sleep(0.05)

    # TA 2 assigns student 3
    await ta2_ws.send(
        json.dumps({"action": "assign_student_to_session", "student_id": "student3"})
    )
    print("TA 2 assigned student 3")
    time.sleep(0.05)

    # TA 2 leaves session
    await ta2_ws.send(json.dumps({"action": "leave_session"}))
    print("TA 2 left session")
    time.sleep(0.05)

    # TA 2 creates a new session
    await ta2_ws.send(json.dumps({"action": "join_session"}))
    print("TA 2 created new session")
    time.sleep(0.05)

    # TA 1 removes student 1 from session
    await ta_ws.send(
        json.dumps({"action": "remove_student_from_session", "student_id": "student1"})
    )
    time.sleep(0.05)

    # Student 1 leaves the room completely
    await student1_ws.close()
    print("Student 1 left the room")
    time.sleep(0.05)

    # Student 2 accidently leaves the room
    await student2_ws.close()
    print("Student 2 left the room")
    time.sleep(0.05)

    # Student 2 joins back in
    student2_ws = await connect_user("student2", "Bob", "student")
    print("Student 2 joined back in")
    time.sleep(0.05)

    # TA 1 removes student 3 from session
    await ta_ws.send(
        json.dumps({"action": "remove_student_from_session", "student_id": "student3"})
    )
    print("TA 1 removed student 3 from session")
    time.sleep(0.05)

    # TA 1 removes student 2 from session
    await ta_ws.send(
        json.dumps({"action": "remove_student_from_session", "student_id": "student2"})
    )
    print("TA 1 removed student 2 from session")
    time.sleep(0.05)

    # TA 2 leaves session
    await ta2_ws.send(json.dumps({"action": "leave_session"}))
    print("TA 2 left session")
    time.sleep(0.05)

    # TA 1 leaves session
    await ta_ws.send(json.dumps({"action": "leave_session"}))
    print("TA 1 left session")
    time.sleep(0.05)

    # TA 2 joins session
    await ta2_ws.send(json.dumps({"action": "join_session"}))
    print("TA 2 joined session")
    time.sleep(0.05)

    # Student 2 joins queue
    await student2_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 2 joined queue")
    time.sleep(0.05)

    # Student 3 joins queue
    await student3_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 3 joined queue")
    time.sleep(0.05)

    # TA 2 assigns student 2
    await ta2_ws.send(
        json.dumps({"action": "assign_student_to_session", "student_id": "student2"})
    )
    print("TA 2 assigned student 2")
    time.sleep(0.05)

    # TA 2 assigns student 3
    await ta2_ws.send(
        json.dumps({"action": "assign_student_to_session", "student_id": "student3"})
    )
    print("TA 2 assigned student 3")
    time.sleep(0.05)

    # TA 2 leaves session
    await ta2_ws.send(json.dumps({"action": "leave_session"}))
    print("TA 2 left session")
    time.sleep(0.05)

    # student 1 joins back in
    student1_ws = await connect_user("student1", "Alice", "student")
    print("Student 1 joined back in")
    time.sleep(0.05)

    # student 1 joins queue
    await student1_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 1 joined queue")
    time.sleep(0.05)

    # student 1 accidently leaves room
    await student1_ws.close()
    print("Student 1 left the room")
    time.sleep(0.05)

    # student 1 joins back in
    student1_ws = await connect_user("student1", "Alice", "student")
    print("Student 1 joined back in")
    time.sleep(0.05)

    # Student 1 leaves queue
    await student1_ws.send(json.dumps({"action": "leave_queue"}))
    print("Student 1 left queue")
    time.sleep(0.05)

    # Another ta joins
    ta3_ws = await connect_user("ta3", "Jack TA", "TA")
    print("TA 3 connected")
    time.sleep(0.05)

    # TA 3 joins session
    await ta3_ws.send(json.dumps({"action": "join_session"}))
    print("TA 3 joined session")
    time.sleep(0.05)

    # TA 3 leaves the room accidently
    await ta3_ws.close()
    print("TA 3 left the room")
    time.sleep(0.05)

    # Student 1 joins the queue
    await student1_ws.send(json.dumps({"action": "join_queue"}))
    print("Student 1 joined queue")
    time.sleep(0.05)

    # TA 3 joins back in
    ta3_ws = await connect_user("ta3", "Jack TA", "TA")
    print("TA 3 joined back in")
    time.sleep(0.05)

    # TA 3 leaves session
    await ta3_ws.send(json.dumps({"action": "leave_session"}))
    print("TA 3 left session")
    time.sleep(0.05)

    # TA 4 joins a new class
    ta4_ws = await connect_user("ta4", "Jill TA", "TA", "cs102")
    print("TA 4 connected")
    time.sleep(0.05)

    # TA 4 joins session
    await ta4_ws.send(json.dumps({"action": "join_session"}))
    print("TA 4 joined session")
    time.sleep(0.05)

    # student 1 leaves queue
    await student1_ws.send(json.dumps({"action": "leave_queue"}))
    print("Student 1 left queue")
    time.sleep(0.05)


if __name__ == "__main__":
    asyncio.run(basic_test())
