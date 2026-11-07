from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Optional


class Role(IntEnum):
    GUEST = 0
    USER = 10
    POWER = 50
    ADMIN = 100


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: Role = Role.USER
    display_name: str = ""
    is_active: bool = True
    must_change_password: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    def check_password(self, password: str) -> bool:
        return _verify_password(password, self.password_hash)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return f"pbkdf2_sha256$260000${salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return secrets.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


class UserStore:
    def __init__(self, db_path: str | Path = "data/omnisearch.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role INTEGER NOT NULL DEFAULT 10,
                    display_name TEXT DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    must_change_password INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT,
                    last_login TEXT
                )
                """
            )
            conn.commit()

    def create_user(
        self,
        username: str,
        password: str,
        role: Role = Role.USER,
        display_name: str = "",
        must_change_password: bool = False,
    ) -> User:
        password_hash = _hash_password(password)
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO users (username, password_hash, role, display_name, is_active, must_change_password, created_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (username, password_hash, int(role), display_name or username, int(must_change_password), now),
            )
            conn.commit()
            return self.get_user(cur.lastrowid)

    def get_user(self, user_id: int) -> Optional[User]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return self._row_to_user(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return self._row_to_user(row) if row else None

    def list_users(self) -> list[User]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
            return [self._row_to_user(r) for r in rows]

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        allowed = {"display_name", "role", "is_active", "must_change_password", "password"}
        fields = []
        values = []
        for k, v in kwargs.items():
            if k not in allowed:
                continue
            if k == "password":
                fields.append("password_hash = ?")
                values.append(_hash_password(v))
            elif k == "role":
                fields.append("role = ?")
                values.append(int(v))
            else:
                fields.append(f"{k} = ?")
                values.append(v)
        if not fields:
            return self.get_user(user_id)
        values.append(user_id)
        with self._conn() as conn:
            conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()
        return self.get_user(user_id)

    def record_login(self, user_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), user_id),
            )
            conn.commit()

    def _row_to_user(self, row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=Role(row["role"]),
            display_name=row["display_name"] or "",
            is_active=bool(row["is_active"]),
            must_change_password=bool(row["must_change_password"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None,
        )
