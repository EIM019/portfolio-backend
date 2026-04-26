import json
from database import get_connection


SEED_PROJECTS = [
  {
    "title": "xBankz",
    "description": "A secure fintech banking platform with fraud detection and role-based access control.",
    "problem": "Users needed a realistic digital banking experience with proper security and transfer controls.",
    "solution": "Built a full-stack banking app with OTP authentication, transfer workflows, and automated fraud detection.",
    "features": ["OTP login with account lockout", "Internal and interbank transfers with admin approval", "Fraud detection and audit trail logging"],
    "tech_stack": ["React", "Flask", "PostgreSQL"],
    "image_url": "https://i.imgur.com/8jQtaD1.jpg",
    "live_url": "https://project-xbanz-frontend.vercel.app",
    "category": "Web Apps",
    "featured": 1
  }
]


def seed_projects_if_empty():
  with get_connection() as conn:
    existing = conn.execute("SELECT COUNT(*) AS count FROM projects").fetchone()["count"]
    if existing > 0:
      return

    for project in SEED_PROJECTS:
      conn.execute(
        """
        INSERT INTO projects
        (title, description, problem, solution, features, tech_stack, image_url, live_url, category, featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          project["title"],
          project["description"],
          project["problem"],
          project["solution"],
          json.dumps(project["features"]),
          json.dumps(project["tech_stack"]),
          project["image_url"],
          project["live_url"],
          project["category"],
          project["featured"]
        )
      )