# auth/session_store.py — file-based session persistence

import json
import uuid
from pathlib import Path

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)


def save_session(user: dict, access: str, refresh: str) -> str:
    """Save session data to a file. Returns session_id."""
    session_id = uuid.uuid4().hex
    data = {"access": access, "refresh": refresh, "user": user}
    (SESSION_DIR / f"{session_id}.json").write_text(json.dumps(data))
    return session_id


def load_session(session_id: str) -> dict | None:
    """Load session data from file. Returns None if not found."""
    path = SESSION_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def delete_session(session_id: str):
    """Delete a session file."""
    path = SESSION_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
