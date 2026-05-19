import os
import sqlite3
from contextlib import contextmanager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "portfolio.db")


@contextmanager
def get_connection():
  connection = sqlite3.connect(DB_PATH)
  connection.row_factory = sqlite3.Row
  try:
    yield connection
    connection.commit()
  finally:
    connection.close()


def init_db():
  with get_connection() as conn:
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        problem TEXT NOT NULL,
        solution TEXT NOT NULL,
        features TEXT NOT NULL,
        tech_stack TEXT NOT NULL,
        image_url TEXT NOT NULL,
        live_url TEXT NOT NULL,
        category TEXT NOT NULL,
        featured INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
      """
    )
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
      """
    )
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS login_otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        otp_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT,
        request_ip TEXT,
        user_agent TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
      """
    )
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        session_token_hash TEXT NOT NULL,
        login_ip TEXT,
        user_agent TEXT,
        login_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL
      )
      """
    )
