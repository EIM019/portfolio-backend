import json
from database import get_connection


SEED_PROJECTS = [
  {
    "title": "Campus Event Hub",
    "description": "A student event discovery platform with role-based dashboards.",
    "problem": "Students missed key events due to fragmented updates.",
    "solution": "Centralized all event posts with RSVP and smart filtering.",
    "features": ["Role-based auth", "Event analytics", "RSVP workflow"],
    "tech_stack": ["React", "Flask", "SQLite"],
    "image_url": "https://picsum.photos/seed/eventhub/1200/675",
    "live_url": "https://example.com",
    "category": "School Projects",
    "featured": 1
  },
  {
    "title": "Client Invoice Portal",
    "description": "Invoice and payment tracking tool for freelance projects.",
    "problem": "Manual invoicing made follow-ups and due-date tracking hard.",
    "solution": "A dashboard for invoice creation, status tracking, and exports.",
    "features": ["Invoice templates", "Status tracking", "PDF export"],
    "tech_stack": ["React", "Python", "SQLite"],
    "image_url": "https://picsum.photos/seed/invoice/1200/675",
    "live_url": "https://example.com",
    "category": "Client Work",
    "featured": 1
  },
  {
    "title": "TaskFlow Web App",
    "description": "A keyboard-first team task board with filtered views.",
    "problem": "Teams needed a faster workflow than heavy PM platforms.",
    "solution": "Built a lean board with statuses, labels, and quick search.",
    "features": ["Kanban board", "Search filters", "Keyboard shortcuts"],
    "tech_stack": ["React", "Flask", "SQLite"],
    "image_url": "https://picsum.photos/seed/taskflow/1200/675",
    "live_url": "https://example.com",
    "category": "Web Apps",
    "featured": 0
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
