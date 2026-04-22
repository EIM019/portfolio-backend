import json
from database import get_connection


def _project_row_to_dict(row):
  return {
    "id": row["id"],
    "title": row["title"],
    "description": row["description"],
    "problem": row["problem"],
    "solution": row["solution"],
    "features": json.loads(row["features"]),
    "tech_stack": json.loads(row["tech_stack"]),
    "image_url": row["image_url"],
    "live_url": row["live_url"],
    "category": row["category"],
    "featured": bool(row["featured"]),
    "created_at": row["created_at"]
  }


def get_projects():
  with get_connection() as conn:
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    return [_project_row_to_dict(row) for row in rows]


def get_project_by_id(project_id):
  with get_connection() as conn:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _project_row_to_dict(row) if row else None


def create_contact(name, email, message):
  with get_connection() as conn:
    conn.execute(
      "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
      (name.strip(), email.strip(), message.strip())
    )
