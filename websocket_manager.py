from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
from collections import OrderedDict


class Student:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, Student):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class TA:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.current_session: str = None  # Session ID

    def __eq__(self, other):
        if not isinstance(other, TA):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Session:
    def __init__(self, host_ta: TA):
        self.tas: Set[TA] = {host_ta}  # Host TA is always in the session
        host_ta.current_session = host_ta.id
        self.students: Set[Student] = set()  # Students in the session
        self.id = host_ta.id  # Using host TA's ID as session ID

    def add_ta(self, ta: TA) -> None:
        """Add another TA to the session"""
        self.tas.add(ta)
        ta.current_session = self.id

    def remove_ta(self, ta: TA) -> None:
        """Remove a TA from the session"""
        self.tas.remove(ta)
        ta.current_session = None

    def add_student(self, student: Student) -> None:
        """Add a student to the session"""
        self.students.add(student)

    def remove_student(self, student: Student) -> None:
        """Remove a student from the session"""
        self.students.remove(student)

    @property
    def student_ids(self) -> List[str]:
        """Get the IDs of all students in the session"""
        return [student.id for student in self.students]

    @property
    def ta_ids(self) -> List[str]:
        """Get the IDs of all TAs in the session"""
        return [ta.id for ta in self.tas]


class OfficeHourRoom:
    def __init__(self, class_id: str):
        self.connections: Dict[str, WebSocket] = {}  # user ID -> WebSocket

        self.class_id = class_id  # Class ID
        self.students: Dict[str, Student] = {}  # Student ID -> Student
        self.tas: Dict[str, TA] = {}  # TA ID -> TA

        self.queue = OrderedDict()  # Student ID -> Student
        self.sessions: Dict[
            str, Session
        ] = {}  # Session ID (same as host TA id) -> Session

    async def broadcast_state(self):
        """Broadcast current state to all connected users"""
        state = {
            "class_id": self.class_id,
            "students": [
                {"id": student.id, "name": student.name}
                for student in self.students.values()
            ],
            "tas": [{"id": ta.id, "name": ta.name} for ta in self.tas.values()],
            "queue": [
                {"id": student.id, "name": student.name}
                for student in self.queue.values()
            ],
            "sessions": [
                {
                    "session_id": session.id,
                    "session_tas": session.ta_ids,
                    "session_students": session.student_ids,
                }
                for session in self.sessions.values()
            ],
        }

        connections = dict(self.connections)
        for user_id, connection in connections.items():
            try:
                await connection.send_json(state)
            except WebSocketDisconnect:
                if user_id in self.connections:
                    del self.connections[user_id]


class OfficeHourManager:
    def __init__(self):
        self.rooms: Dict[str, OfficeHourRoom] = {}

    def get_or_create_room(self, class_id: str) -> OfficeHourRoom:
        if class_id not in self.rooms:
            self.rooms[class_id] = OfficeHourRoom(class_id)
        return self.rooms[class_id]
