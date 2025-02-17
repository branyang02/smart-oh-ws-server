import uuid
from fastapi import WebSocket, WebSocketDisconnect
from typing import Literal, TypedDict, Union
from typing import Dict, List
from collections import OrderedDict

type User = Union[Student, TA]


class UserState(TypedDict):
    id: str
    columnId: str  # Session ID | "queue" | "none"
    name: str
    type: Literal["student", "TA"]


class ColumnState(TypedDict):
    id: str
    title: str


class RoomState(TypedDict):
    classId: str
    allUsers: List[UserState]
    users: List[UserState]
    columns: List[ColumnState]


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


class Queue:
    def __init__(self):
        self.users_list: List[str] = []  # Student IDs
        self.users_dict: Dict[str, Student] = {}  # Student ID -> Student

    def add_student(self, student: Student, index: int = None) -> None:
        if student.id in self.users_dict:
            raise ValueError("Student is already in the queue")

        student.current_location = "queue"
        if index is None or index >= len(self.users_list):
            self.users_list.append(student.id)
        else:
            self.users_list.insert(index, student.id)
        self.users_dict[student.id] = student

    def remove_student(self, student: Student) -> None:
        if student.id not in self.users_dict:
            raise ValueError("Student is not in the queue")

        self.users_list.remove(student.id)
        del self.users_dict[student.id]
        student.current_location = None

    @property
    def users_state(self) -> List[UserState]:
        return [
            {
                "id": user_id,
                "columnId": "queue",
                "name": self.users_dict[user_id].name,
                "type": "student",
            }
            for user_id in self.users_list
        ]


class Session:
    def __init__(self, id: str = None):
        self.id = id
        self.users_list: List[str] = []  # User IDs
        self.users_dict: Dict[str, User] = {}  # User ID -> User

    def add_ta(self, ta: TA, index: int = None) -> None:
        if ta.id in self.users_dict:
            raise ValueError("TA is already in the session")

        ta.current_location = self.id
        if index is None or index >= len(self.users_list):
            self.users_list.append(ta.id)
        else:
            self.users_list.insert(index, ta.id)
        self.users_dict[ta.id] = ta

    def remove_ta(self, ta: TA) -> None:
        if ta.id not in self.users_dict:
            raise ValueError("TA is not in the session")

        self.users_list.remove(ta.id)
        del self.users_dict[ta.id]
        ta.current_location = None

    def add_student(self, student: Student, index: int = None) -> None:
        if student.id in self.users_dict:
            raise ValueError("Student is already in the session")

        student.current_location = self.id
        if index is None or index >= len(self.users_list):
            self.users_list.append(student.id)
        else:
            self.users_list.insert(index, student.id)
        self.users_dict[student.id] = student

    def remove_student(self, student: Student) -> None:
        if student.id not in self.users_dict:
            raise ValueError("Student is not in the session")

        self.users_list.remove(student.id)
        del self.users_dict[student.id]
        student.current_location = None

    @property
    def student_ids(self) -> List[str]:
        """Get the IDs of all students in the session"""
        return [
            user.id for user in self.users_dict.values() if isinstance(user, Student)
        ]

    @property
    def ta_ids(self) -> List[str]:
        """Get the IDs of all TAs in the session"""
        return [user.id for user in self.users_dict.values() if isinstance(user, TA)]

    @property
    def users_state(self) -> List[UserState]:
        return [
            {
                "id": user_id,
                "columnId": self.id,
                "name": self.users_dict[user_id].name,
                "type": "TA" if isinstance(self.users_dict[user_id], TA) else "student",
            }
            for user_id in self.users_list
        ]


class OfficeHourRoom:
    def __init__(self, class_id: str):
        self.connections: Dict[str, WebSocket] = {}  # user ID -> WebSocket

        self.class_id = class_id  # Class ID
        self.students: Dict[str, Student] = {}  # Student ID -> Student
        self.tas: Dict[str, TA] = {}  # TA ID -> TA

        self.queue = Queue()
        self.sessions: OrderedDict[str, Session] = {}  # Session ID -> Session

    @property
    def users_state(self) -> List[UserState]:
        return [
            {
                "id": student.id,
                "columnId": "none",
                "name": student.name,
                "type": "student",
            }
            for student in self.students.values()
        ] + [
            {"id": ta.id, "columnId": "none", "name": ta.name, "type": "TA"}
            for ta in self.tas.values()
        ]

    @property
    def queue_users_state(self) -> List[UserState]:
        return self.queue.users_state

    @property
    def session_users_state(self) -> List[UserState]:
        return sum([session.users_state for session in self.sessions.values()], [])

    async def broadcast_state(self):
        """Broadcast current state to all connected users. Consistent with frontend types."""
        state: RoomState = {
            "classId": self.class_id,
            "allUsers": self.users_state,
            "users": self.queue_users_state + self.session_users_state,
            "columns": [
                {
                    "id": "queue",
                    "title": "Queue",
                }
            ]
            + [
                {
                    "id": session.id,
                    "title": session.id,
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
        self.rooms: Dict[str, OfficeHourRoom] = {}  # Class ID -> OfficeHourRoom

    def get_or_create_room(self, class_id: str) -> OfficeHourRoom:
        if class_id not in self.rooms:
            self.rooms[class_id] = OfficeHourRoom(class_id)
        return self.rooms[class_id]
