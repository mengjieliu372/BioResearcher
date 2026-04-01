from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import time
import uuid

from app.auth_core import (
    SUPERUSER_STUDENT_ID,
    ensure_example_access,
    ensure_example_project_exists,
    hash_password,
    init_auth_db,
    is_valid_student_id,
    new_salt,
    require_user,
    _db_conn,
)


router = APIRouter(prefix="/auth")


class RegisterPayload(BaseModel):
    username: str
    password: str
    display_name: str | None = None


class LoginPayload(BaseModel):
    username: str
    password: str


@router.on_event("startup")
def _startup_init_auth_db():
    init_auth_db()
    ensure_example_project_exists()


init_auth_db()
ensure_example_project_exists()


def _invalid_credentials():
    raise HTTPException(status_code=401, detail="账号密码错误")


@router.post("/register")
async def register(payload: RegisterPayload):
    username = (payload.username or "").strip()
    password = payload.password or ""
    display_name = (payload.display_name or "").strip() or username
    if not is_valid_student_id(username):
        _invalid_credentials()
    if not password:
        _invalid_credentials()

    salt = new_salt()
    pwd_hash = hash_password(password, salt)
    now = int(time.time())
    is_super = 1 if username == SUPERUSER_STUDENT_ID else 0
    conn = _db_conn()
    try:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (username, password_salt, password_hash, display_name, created_at, is_superuser)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, salt, pwd_hash, display_name, now, is_super),
            )
            conn.commit()
            user_id = int(cur.lastrowid)
        except Exception:
            raise HTTPException(status_code=409, detail="账号已存在")
    finally:
        conn.close()
    ensure_example_access(user_id)
    return {"ok": True, "user_id": user_id, "username": username, "display_name": display_name}


@router.post("/login")
async def login(payload: LoginPayload):
    username = (payload.username or "").strip()
    password = payload.password or ""
    if not is_valid_student_id(username):
        _invalid_credentials()
    if not password:
        _invalid_credentials()

    now = int(time.time())
    conn = _db_conn()
    try:
        row = conn.execute(
            "SELECT id, username, display_name, password_salt, password_hash, is_superuser FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        is_new_user = False
        if row is None:
            # 无感注册：首次登录即创建账号
            salt = new_salt()
            pwd_hash = hash_password(password, salt)
            is_super = 1 if username == SUPERUSER_STUDENT_ID else 0
            cur = conn.execute(
                """
                INSERT INTO users (username, password_salt, password_hash, display_name, created_at, is_superuser)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, salt, pwd_hash, username, now, is_super),
            )
            conn.commit()
            user_id = int(cur.lastrowid)
            row = conn.execute(
                "SELECT id, username, display_name, password_salt, password_hash, is_superuser FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            is_new_user = True
        else:
            calc = hash_password(password, row["password_salt"])
            if calc != row["password_hash"]:
                _invalid_credentials()

        # 指定学工号强制超级用户
        if username == SUPERUSER_STUDENT_ID and int(row["is_superuser"] or 0) != 1:
            conn.execute("UPDATE users SET is_superuser = 1 WHERE id = ?", (int(row["id"]),))
            conn.commit()
            row = conn.execute(
                "SELECT id, username, display_name, password_salt, password_hash, is_superuser FROM users WHERE id = ?",
                (int(row["id"]),),
            ).fetchone()

        token = uuid.uuid4().hex + uuid.uuid4().hex
        expires_at = now + 7 * 24 * 3600
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, int(row["id"]), now, expires_at),
        )
        conn.commit()
        ensure_example_access(int(row["id"]))

        welcome = f"{username}，欢迎注册" if is_new_user else f"{username}，欢迎回来"
        return {
            "ok": True,
            "token": token,
            "expires_at": expires_at,
            "welcome_message": welcome,
            "is_new_user": is_new_user,
            "user": {
                "id": int(row["id"]),
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "is_superuser": bool(int(row["is_superuser"] or 0)),
            },
        }
    finally:
        conn.close()


@router.get("/me")
async def me(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    return {"ok": True, "user": user}


@router.post("/logout")
async def logout(authorization: str | None = Header(default=None)):
    token = None
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
    if token:
        conn = _db_conn()
        try:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()
    return {"ok": True}

