import datetime
import os

from dotenv import load_dotenv
from psycopg2 import pool

from src.websocket.state import User

# Load .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv("DATABASE_URL")

# Create a connection pool
connection_pool = pool.SimpleConnectionPool(
    1,  # Minimum number of connections in the pool
    10,  # Maximum number of connections in the pool
    connection_string,
)


def get_user_by_session_token(session_token: str) -> User | None:
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "userId", "expires"
                FROM "session"
                WHERE "sessionToken" = %s
                LIMIT 1
                """,
                (session_token,),
            )
            session_row = cur.fetchone()

            if not session_row:
                return None

            user_id, expires = session_row

            # 2) Check expiration
            now_utc = datetime.datetime.utcnow()
            if expires < now_utc:
                return None

            # 3) Now that the session is valid, retrieve the user record
            cur.execute(
                """
                SELECT "id", "name", "email", "emailVerified", "image"
                FROM "user"
                WHERE "id" = %s
                LIMIT 1
                """,
                (user_id,),
            )
            user_row = cur.fetchone()

            if not user_row:
                return None
            user = User(
                id=user_row[0],
                name=user_row[1],
                email=user_row[2],
                emailVerified=user_row[3],
                image=user_row[4],
            )

            return user
    finally:
        connection_pool.putconn(conn)


def get_role_by_user_id_class_id(user_id: str, class_id: str) -> str | None:
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT "role"
                FROM "user_class"
                WHERE "user_id" = %s AND "class_id" = %s
                LIMIT 1
                """,
                (user_id, class_id),
            )
            role_row = cur.fetchone()

            if not role_row:
                return None

            return role_row[0]
    finally:
        connection_pool.putconn(conn)
