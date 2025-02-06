from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from websocket_manager import OfficeHourManager, Session, Student, TA

app = FastAPI()
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
                student = room.students[user_id]
                room.queue[user_id] = student  # Add student to queue

            elif action == "leave_queue" and user_type == "student":
                if user_id in room.queue:
                    del room.queue[user_id]
                else:
                    raise ValueError("Student not in queue")

            elif action == "join_session" and user_type == "TA":
                session_id = data.get("session_id")
                ta = room.tas[user_id]

                if session_id is not None and session_id in room.sessions:
                    room.sessions[session_id].add_ta(ta)
                else:
                    if user_id not in room.sessions:
                        room.sessions[user_id] = Session(
                            ta
                        )  # Create new session with TA as host
                    room.sessions[user_id].add_ta(
                        ta
                    )  # Add TA to session if not already in one

            elif action == "leave_session" and user_type == "TA":
                ta = room.tas[user_id]
                if ta.current_session:
                    cur_session_id = ta.current_session
                    session = room.sessions[cur_session_id]
                    session.remove_ta(ta)
                    # If session is empty, remove it
                    if len(session.tas) == 0:
                        del room.sessions[cur_session_id]

            elif action == "assign_student_to_session" and user_type == "TA":
                ta = room.tas[user_id]
                student_id = data["student_id"]

                if not ta.current_session:
                    raise ValueError("TA not in a session")
                if student_id not in room.students:
                    raise ValueError("Student not found in room")

                student = room.students[student_id]
                session = room.sessions[ta.current_session]

                if student_id not in room.queue:
                    raise ValueError("Student not in queue")

                session.add_student(student)
                del room.queue[student_id]

            elif action == "remove_student_from_session" and user_type == "TA":
                ta = room.tas[user_id]
                student_id = data["student_id"]

                if not ta.current_session:
                    raise ValueError("TA not in a session")
                if student_id not in room.students:
                    raise ValueError("Student not found in room")
                if student_id not in room.sessions[ta.current_session].student_ids:
                    raise ValueError("Student not in session")

                student = room.students[student_id]
                session = room.sessions[ta.current_session]
                session.remove_student(student)

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
        # Fully disconnect user if they are in room.tas or room.students
        # Perserve their spot if they are in the queue or a session
        if not (
            user_id in room.queue
            or any(
                user_id in session.student_ids or user_id in session.ta_ids
                for session in room.sessions.values()
            )
        ):
            if user_id in room.tas:
                del room.tas[user_id]
            if user_id in room.students:
                del room.students[user_id]

        if user_id in room.connections:
            del room.connections[user_id]
        if room.connections:
            await room.broadcast_state()
