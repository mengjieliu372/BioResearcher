from __future__ import annotations

import hashlib
import json
import random
import secrets
import sqlite3
import time
import uuid
from pathlib import Path

from fastapi import Header, HTTPException

DB_PATH = Path(__file__).parent / "data" / "auth.db"
EXPERIMENTS_PATH = Path(__file__).parent / "data" / "experiments.json"
SUPERUSER_STUDENT_ID = "37220232203875"
EXAMPLE_PROJECT_ID = 94127
EXAMPLE_PROJECT_NAME = "Example"


def _db_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str):
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    names = {str(c[1]) for c in cols}
    if column not in names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_auth_db():
    conn = _db_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                created_at INTEGER NOT NULL
            )
            """
        )
        _ensure_column(conn, "users", "is_superuser", "is_superuser INTEGER NOT NULL DEFAULT 0")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_project_access (
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                alias_name TEXT,
                granted_at INTEGER NOT NULL,
                PRIMARY KEY (user_id, project_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return digest.hex()


def new_salt() -> str:
    return secrets.token_hex(16)


def extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def is_valid_student_id(username: str) -> bool:
    return username.isdigit() and 10 <= len(username) <= 14


def ensure_example_access(user_id: int):
    now = int(time.time())
    conn = _db_conn()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_project_access (user_id, project_id, alias_name, granted_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, EXAMPLE_PROJECT_ID, EXAMPLE_PROJECT_NAME, now),
        )
        conn.commit()
    finally:
        conn.close()


def require_user(authorization: str | None):
    token = extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    now = int(time.time())
    conn = _db_conn()
    try:
        row = conn.execute(
            """
            SELECT s.token, u.id AS user_id, u.username, u.display_name, u.is_superuser, s.expires_at
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid session")
        if int(row["expires_at"]) <= now:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            raise HTTPException(status_code=401, detail="Session expired")
        return {
            "id": int(row["user_id"]),
            "username": row["username"],
            "display_name": row["display_name"] or row["username"],
            "is_superuser": bool(int(row["is_superuser"] or 0)),
            "token": token,
        }
    finally:
        conn.close()


def get_user_project_access_map(user_id: int) -> dict[int, str | None]:
    conn = _db_conn()
    try:
        rows = conn.execute(
            "SELECT project_id, alias_name FROM user_project_access WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return {int(r["project_id"]): (r["alias_name"] if r["alias_name"] else None) for r in rows}
    finally:
        conn.close()


def user_can_access_project(user: dict, project_id: int) -> bool:
    if bool(user.get("is_superuser", False)):
        return True
    access = get_user_project_access_map(int(user["id"]))
    return int(project_id) in access


def ensure_project_access(user: dict, project_id: int):
    if user_can_access_project(user, project_id):
        return
    raise HTTPException(status_code=403, detail="No permission to access this project")


def list_projects_for_user(user: dict, all_projects: list[dict]) -> list[dict]:
    if bool(user.get("is_superuser", False)):
        out = []
        for p in all_projects:
            x = dict(p)
            x.setdefault("owner_username", x.get("owner_username") or "system")
            out.append(x)
        return out

    access_map = get_user_project_access_map(int(user["id"]))
    username = str(user.get("username") or "")
    # Backward compatibility: if old projects already recorded owner_username, auto-grant access.
    for p in all_projects:
        try:
            pid = int(p.get("id"))
        except Exception:
            continue
        owner = str(p.get("owner_username") or "")
        if owner and owner == username and pid not in access_map:
            grant_ts = int(time.time())
            conn = _db_conn()
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO user_project_access (user_id, project_id, alias_name, granted_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (int(user["id"]), pid, None, grant_ts),
                )
                conn.commit()
            finally:
                conn.close()
            access_map[pid] = None

    out = []
    for p in all_projects:
        pid = int(p.get("id"))
        if pid not in access_map:
            continue
        x = dict(p)
        alias = access_map.get(pid)
        if alias:
            x["expName"] = alias
        x["owner_username"] = user.get("username")
        out.append(x)
    return out


def _read_experiments() -> list[dict]:
    if not EXPERIMENTS_PATH.exists():
        return []
    with EXPERIMENTS_PATH.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _write_experiments(data: list[dict]):
    EXPERIMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXPERIMENTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def ensure_example_project_exists():
    experiments = _read_experiments()
    if any(int(x.get("id", -1)) == EXAMPLE_PROJECT_ID for x in experiments):
        return
    experiments.append(
        {
            "id": EXAMPLE_PROJECT_ID,
            "expName": EXAMPLE_PROJECT_NAME,
            "expPurpose": "Example shared project",
            "expCondition": "System prepared example project",
            "expRequirement": "System prepared example project",
            "paperset": {"PMC": True, "PubMed": False},
            "dataset": {"GEO": True, "NCBI": False, "cBioPortal": False},
            "llmModel": "chatgpt5.x",
            "refNum": None,
            "reviewerRound": None,
            "fileNames": [],
            "owner_username": "system",
            "page_search_paper": True,
            "page_search_datasets": True,
            "page_Literature_processing": True,
            "page_design_1": True,
            "page_design_2": True,
            "page_design_3": True,
            "page_dry_1": True,
            "page_dry_2": True,
            "page_dry_3": True,
            "page_coding_1": True,
            "page_coding_2": True,
            "page_coding_3": True,
        }
    )
    _write_experiments(experiments)


def create_user_project_record(username: str, exp_name: str, exp_purpose: str, exp_condition: str, exp_requirement: str, payload: dict) -> dict:
    return {
        "id": payload["id"],
        "expName": exp_name,
        "expPurpose": exp_purpose,
        "expCondition": exp_condition,
        "expRequirement": exp_requirement,
        "paperset": payload["paperset"],
        "dataset": payload["dataset"],
        "llmModel": payload["llmModel"],
        "refNum": payload.get("refNum"),
        "reviewerRound": payload.get("reviewerRound"),
        "fileNames": payload.get("fileNames", []),
        "owner_username": username,
    }


def generate_unique_experiment_id(existing: set[int]) -> int:
    while True:
        nid = random.randint(10000, 99999)
        if nid not in existing:
            return nid
