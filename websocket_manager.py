from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from collections import OrderedDict


class Student:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.current_location: str = None  # Session ID | "queue"


class TA:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.current_location: str = None  # Session ID


class Queue(OrderedDict):
    """Student Queue

    Args:
        OrderedDict: Student ID -> Student
    """

    def __init__(self, init_queue: OrderedDict = None):
        super().__init__(init_queue or OrderedDict())

    def add_student(self, student: Student) -> None:
        self[student.id] = student
        student.current_location = "queue"

    def remove_student(self, student: Student) -> None:
        del self[student.id]
        student.current_location = None


class Session:
    def __init__(self, id: str):
        self.id: str = id

        self.tas = OrderedDict()  # TA ID -> TA
        self.students = OrderedDict()  # Student ID -> Student

    def add_ta(self, ta: TA) -> None:
        """Add another TA to the session"""
        self.tas[ta.id] = ta
        ta.current_location = self.id

    def remove_ta(self, ta: TA) -> None:
        """Remove a TA from the session"""
        del self.tas[ta.id]
        ta.current_location = None

    def add_student(self, student: Student) -> None:
        """Add a student to the session"""
        self.students[student.id] = student
        student.current_location = self.id

    def remove_student(self, student: Student) -> None:
        """Remove a student from the session"""
        del self.students[student.id]
        student.current_location = None

    @property
    def student_ids(self) -> List[str]:
        """Get the IDs of all students in the session"""
        return list(self.students.keys())

    @property
    def ta_ids(self) -> List[str]:
        """Get the IDs of all TAs in the session"""
        return list(self.tas.keys())

    @property
    def users_state(self):
        return [
            {
                "id": student.id,
                "name": student.name,
                "type": "student",
                "location": self.id,
            }
            for student in self.students.values()
        ] + [
            {"id": ta.id, "name": ta.name, "type": "TA", "location": self.id}
            for ta in self.tas.values()
        ]


class OfficeHourRoom:
    def __init__(self, class_id: str):
        self.connections: Dict[str, WebSocket] = {}  # user ID -> WebSocket

        self.class_id = class_id  # Class ID
        self.students: Dict[str, Student] = {}  # Student ID -> Student
        self.tas: Dict[str, TA] = {}  # TA ID -> TA

        self.queue = Queue()  # Student ID -> Student
        self.sessions: Dict[str, Session] = {}  # Session ID -> Session

    @property
    def users_state(self):
        return [
            {"id": student.id, "name": student.name, "type": "student"}
            for student in self.students.values()
        ] + [{"id": ta.id, "name": ta.name, "type": "TA"} for ta in self.tas.values()]

    @property
    def queue_state(self):
        return [
            {
                "id": student.id,
                "name": student.name,
                "type": "student",
                "location": "queue",
            }
            for student in self.queue.values()
        ]

    @property
    def sessions_state(self):
        return {
            session.id: {
                "id": session.id,
                "users": session.users_state,
            }
            for session in self.sessions.values()
        }

    async def broadcast_state(self):
        """Broadcast current state to all connected users. Consistent with frontend types."""
        state = {
            "class_id": self.class_id,
            "all_users": self.users_state,
            "queue": self.queue_state,
            "sessions": self.sessions_state,
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
        self.rooms: Dict[str, OfficeHourRoom] = {}  # Class ID -> OfficeHourRoom

    def get_or_create_room(self, class_id: str) -> OfficeHourRoom:
        if class_id not in self.rooms:
            self.rooms[class_id] = OfficeHourRoom(class_id)
        return self.rooms[class_id]
