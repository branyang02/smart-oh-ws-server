import uuid
from collections import OrderedDict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


from websocket_manager import OfficeHourManager, Queue, Session, Student, TA
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


@app.websocket("/ws/{class_id}/{user_id}")
async def office_hour_websocket(
    websocket: WebSocket, class_id: str, user_id: str, user_type: str, name: str
):
    room = manager.get_or_create_room(class_id)
    await websocket.accept()
    room.connections[user_id] = websocket

    try:
        if user_type == "TA":
            # Restore or create TA state
            if user_id not in room.tas:
                room.tas[user_id] = TA(user_id, name)
        elif user_type == "student":
            # Restore or create student state
            if user_id not in room.students:
                room.students[user_id] = Student(user_id, name)

        await room.broadcast_state()

        while True:
            data = await websocket.receive_json()
            action = data["action"]

            if action == "join_queue" and user_type == "student":
                """
                - {action: "join_queue"}
                """
                assert user_id in room.students
                student = room.students[user_id]
                assert student.current_location is None
                room.queue.add_student(student)

            elif action == "leave_queue" and user_type == "student":
                """
                - {action: "leave_queue"}
                """
                assert user_id in room.students
                assert user_id in room.queue
                student = room.students[user_id]
                assert student.current_location == "queue"
                room.queue.remove_student(student)

            elif action == "create_session_with_id" and user_type == "TA":
                """
                - {action: "create_session_with_id", new_session_id: "session-..."}
                """
                new_session_id = data.get("new_session_id")
                assert new_session_id not in room.sessions
                assert user_id in room.tas
                ta = room.tas[user_id]
                assert new_session_id not in room.sessions
                new_session = Session(new_session_id)
                room.sessions[new_session_id] = new_session

                if ta.current_location is not None:
                    prev_session = room.sessions[ta.current_location]
                    prev_session.remove_ta(ta)
                    if len(prev_session.ta_ids) == 0:
                        del room.sessions[prev_session.id]

                new_session.add_ta(ta)

            elif action == "create_session" and user_type == "TA":
                """
                TA creates and joins a new session, leaving the previous one if they were in one
                - {action: "create_session"}
                """
                assert user_id in room.tas
                ta = room.tas[user_id]
                new_session_id = f"session-{uuid.uuid4()}"
                assert new_session_id not in room.sessions
                new_session = Session(new_session_id)
                room.sessions[new_session_id] = new_session

                if ta.current_location is not None:
                    prev_session = room.sessions[ta.current_location]
                    prev_session.remove_ta(ta)
                    if len(prev_session.ta_ids) == 0:
                        del room.sessions[prev_session.id]

                new_session.add_ta(ta)

            elif action == "join_session" and user_type == "TA":
                """
                TA joins a new session, leaving the previous one if they were in one
                - {action: "join_session", new_session_id: "ta1"}
                """
                new_session_id = data.get("new_session_id")
                assert new_session_id in room.sessions
                assert user_id in room.tas
                ta = room.tas[user_id]

                if ta.current_location is not None:
                    prev_session = room.sessions[ta.current_location]
                    prev_session.remove_ta(ta)
                    if len(prev_session.ta_ids) == 0:
                        del room.sessions[prev_session.id]

                room.sessions[new_session_id].add_ta(ta)

            elif action == "leave_session" and user_type == "TA":
                """
                This is used when a TA wants to leave a session completely. If a TA wants to switch session, they can call join_session instead.
                {action: "leave_session"}
                """
                assert user_id in room.tas
                ta = room.tas[user_id]
                assert ta.current_location is not None
                session = room.sessions[ta.current_location]
                session.remove_ta(ta)
                # If the session is empty, remove it
                if len(session.ta_ids) == 0:
                    del room.sessions[session.id]

            elif action == "assign_student_to_session" and user_type == "TA":
                """
                {action: "assign_student_to_session", student_id: "student1", session_id: "session-..."}
                """
                assert user_id in room.tas
                student_id = data.get("student_id")
                session_id = data.get("session_id")
                assert student_id in room.students
                assert session_id in room.sessions
                ta = room.tas[user_id]
                student = room.students[student_id]
                session = room.sessions[session_id]

                assert student.current_location is not None

                if student.current_location == "queue":
                    assert student_id in room.queue
                    room.queue.remove_student(student)
                elif student.current_location in room.sessions:
                    prev_session = room.sessions[student.current_location]
                    prev_session.remove_student(student)

                session.add_student(student)

            elif action == "remove_student_from_session" and user_type == "TA":
                """
                {action: "remove_student_from_session", student_id: "student1"}
                """
                assert user_id in room.tas
                student_id = data.get("student_id")
                assert student_id in room.students
                student = room.students[student_id]
                assert student.current_location in room.sessions
                session = room.sessions[student.current_location]
                session.remove_student(student)

            elif action == "reorder_session" and user_type == "TA":
                """
                {action: "reorder_session", session_id: "session-...", student_ids: ["student1", "student2", ...]}
                """
                assert user_id in room.tas
                session_id = data.get("session_id")
                student_ids = data.get("student_ids")
                assert session_id in room.sessions
                session = room.sessions[session_id]
                assert all(student_id in session.students for student_id in student_ids)
                session.students = OrderedDict(
                    (student_id, session.students[student_id])
                    for student_id in student_ids
                )

            elif action == "reorder_queue" and user_type == "TA":
                """
                {action: "reorder_queue", student_ids: ["student1", "student2", ...]}
                """
                assert user_id in room.tas
                student_ids = data.get("student_ids")
                assert all(student_id in room.queue for student_id in student_ids)
                room.queue = Queue(
                    OrderedDict(
                        (student_id, room.queue[student_id])
                        for student_id in student_ids
                    )
                )

            await room.broadcast_state()
            print("Room: ", room.class_id)
            print("Connections:", room.connections.keys())
            print("TAs:", room.tas.keys())
            print("Students:", room.students.keys())
            print("Queue:", room.queue.keys())
            print(
                "Sessions TAs:", [session.ta_ids for session in room.sessions.values()]
            )
            print(
                "Sessions Students:",
                [session.student_ids for session in room.sessions.values()],
            )
            print("--" * 30)

    except WebSocketDisconnect:
        """
        - Fully disconnect TA if they are not in a session.
        - Fully disconnect student if they are not in the queue or a session.
        """
        if user_id in room.tas:
            ta = room.tas[user_id]
            if ta.current_location is None:
                del room.tas[user_id]
        elif user_id in room.students:
            student = room.students[user_id]
            if student.current_location is None:
                del room.students[user_id]

        if user_id in room.connections:
            del room.connections[user_id]
        if room.connections:
            await room.broadcast_state()
