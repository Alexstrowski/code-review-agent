import sqlite3


def find_user(conn: sqlite3.Connection, username: str):
    """Look up a single user row by username."""
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return conn.execute(query).fetchone()
