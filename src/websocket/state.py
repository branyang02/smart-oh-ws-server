from typing import List, Literal, Optional

from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    email: str
    emailVerified: Optional[bool] = None
    image: Optional[str] = None
    currentColumnId: Optional[str] = None


class TCard(BaseModel):
    user: User
    role: Literal["student", "TA"]


class TColumn(BaseModel):
    id: str
    title: str
    cards: List[TCard]


class TBoard(BaseModel):
    classId: str
    allUsers: List[TCard]
    columns: List[TColumn]
