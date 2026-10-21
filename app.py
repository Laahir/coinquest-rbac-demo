"""
CoinQuest API: a small demo of role-based access control (RBAC).

CoinQuest is a made-up money-literacy game. It has three roles:
  - player: a kid playing the game
  - parent: can only look at their own child's progress
  - admin:  can manage all users

The idea: every endpoint declares which roles may use it, and one shared
check enforces that. Wrong login = 401. Right login but wrong role = 403.
"""

import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI(
    title="CoinQuest API",
    description="Demo of role-based access control with three roles: player, parent, admin.",
)

# ---------------------------------------------------------------------------
# Fake data (in memory, resets every time the server restarts)
# ---------------------------------------------------------------------------
USERS = {
    "pat": {"password": "player123", "role": "player"},
    "lee": {"password": "player123", "role": "player"},
    "pam": {"password": "parent123", "role": "parent", "children": ["pat"]},
    "ada": {"password": "admin123", "role": "admin"},
}

PROGRESS = {
    "pat": {"lessons_completed": 3, "coins": 120},
    "lee": {"lessons_completed": 1, "coins": 40},
}

LESSONS = [
    {"id": 1, "title": "Needs vs Wants"},
    {"id": 2, "title": "Saving 101"},
    {"id": 3, "title": "How Interest Works"},
]

TOKENS = {}  # token string -> username

bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Figure out who is calling. Missing or bad token -> 401."""
    if creds is None or creds.credentials not in TOKENS:
        raise HTTPException(status_code=401, detail="Not logged in or bad token")
    username = TOKENS[creds.credentials]
    return {"username": username, **USERS[username]}


def require_roles(*allowed_roles):
    """Build a check that only lets certain roles through. Wrong role -> 403."""

    def checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user['role']}' is not allowed here. Needs one of: {list(allowed_roles)}",
            )
        return user

    return checker


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
class LoginBody(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(body: LoginBody):
    user = USERS.get(body.username)
    if user is None or user["password"] != body.password:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    token = secrets.token_hex(16)
    TOKENS[token] = body.username
    return {"token": token, "role": user["role"]}


@app.get("/me")
def me(user=Depends(get_current_user)):
    """Any logged-in user can see who they are."""
    return {"username": user["username"], "role": user["role"]}


@app.get("/lessons")
def list_lessons(user=Depends(require_roles("player", "parent", "admin"))):
    """Everyone logged in can read the lesson list."""
    return LESSONS


@app.post("/progress/complete-lesson")
def complete_lesson(user=Depends(require_roles("player"))):
    """Only players earn progress, and only for themselves."""
    mine = PROGRESS[user["username"]]
    mine["lessons_completed"] += 1
    mine["coins"] += 10
    return mine


@app.get("/children/{child}/progress")
def child_progress(child: str, user=Depends(require_roles("parent"))):
    """Parents can view progress, but only for their OWN children."""
    if child not in user.get("children", []):
        raise HTTPException(status_code=403, detail="That is not your child")
    return {"child": child, **PROGRESS[child]}


@app.get("/admin/users")
def admin_list_users(user=Depends(require_roles("admin"))):
    """Admin only. Never returns passwords."""
    return [{"username": name, "role": data["role"]} for name, data in USERS.items()]


@app.delete("/admin/users/{username}")
def admin_delete_user(username: str, user=Depends(require_roles("admin"))):
    """Admin only."""
    if username not in USERS:
        raise HTTPException(status_code=404, detail="No such user")
    if username == user["username"]:
        raise HTTPException(status_code=400, detail="Admins cannot delete themselves")
    del USERS[username]
    return {"deleted": username}
