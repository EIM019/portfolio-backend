import os
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
from database import get_connection, init_db
from models import create_contact, create_project, get_project_by_id, get_projects
from seed import seed_projects_if_empty


app = Flask(__name__)

cors_origins = [
  origin.strip().rstrip("/")
  for origin in os.getenv("CORS_ORIGIN", "https://portfolio-frontend-ufib.vercel.app").split(",")
  if origin.strip()
]
if "https://portfolio-frontend-ufib.vercel.app" not in cors_origins:
  cors_origins.append("https://portfolio-frontend-ufib.vercel.app")

CORS(app, resources={r"/api/*": {"origins": cors_origins}})
init_db()
seed_projects_if_empty()

OTP_TTL_MINUTES = 20
SESSION_TTL_MINUTES = 20


def utc_now():
  return datetime.now(timezone.utc)


def iso_time(value):
  return value.isoformat()


def hash_secret(value):
  salt = os.getenv("OTP_HASH_SALT", os.getenv("SECRET_KEY", "portfolio-dev-salt"))
  return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


def client_ip():
  forwarded = request.headers.get("X-Forwarded-For", "")
  if forwarded:
    return forwarded.split(",")[0].strip()
  return request.remote_addr or ""


def verify_recaptcha(token, version):
  secret_key = os.getenv(f"RECAPTCHA_{version.upper()}_SECRET_KEY")
  if not secret_key:
    if os.getenv("RECAPTCHA_REQUIRED", "false").lower() == "true":
      return False, f"reCAPTCHA {version} is not configured."
    return True, "reCAPTCHA skipped; secret key not configured."

  if not token:
    return False, "reCAPTCHA token is required."

  try:
    response = requests.post(
      "https://www.google.com/recaptcha/api/siteverify",
      data={"secret": secret_key, "response": token, "remoteip": client_ip()},
      timeout=8
    )
    result = response.json()
  except Exception:
    return False, "Could not verify reCAPTCHA."

  if not result.get("success"):
    return False, "reCAPTCHA verification failed."

  if version.lower() == "v3":
    minimum_score = float(os.getenv("RECAPTCHA_V3_MIN_SCORE", "0.5"))
    if float(result.get("score", 0)) < minimum_score:
      return False, "reCAPTCHA score was too low."

  return True, "reCAPTCHA verified."


def send_contact_email(name, email, message):
  host = os.getenv("SMTP_HOST")
  port = os.getenv("SMTP_PORT")
  username = os.getenv("SMTP_USERNAME")
  password = os.getenv("SMTP_PASSWORD")
  recipient = os.getenv("CONTACT_RECIPIENT_EMAIL")

  if not all([host, port, username, password, recipient]):
    return False, "SMTP not configured; message stored in database."

  mail = MIMEText(
    f"New contact form submission\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}",
    "plain"
  )
  mail["Subject"] = "Portfolio Contact Form Submission"
  mail["From"] = username
  mail["To"] = recipient

  try:
    with smtplib.SMTP(host, int(port)) as server:
      server.starttls()
      server.login(username, password)
      server.sendmail(username, [recipient], mail.as_string())
    return True, "Email sent successfully."
  except Exception as error:
    return False, f"Email failed: {error}"


def send_otp_email(email, otp):
  host = os.getenv("SMTP_HOST")
  port = os.getenv("SMTP_PORT")
  username = os.getenv("SMTP_USERNAME")
  password = os.getenv("SMTP_PASSWORD")
  sender = os.getenv("SMTP_FROM_EMAIL", username)

  if not all([host, port, username, password, sender]):
    return False, "SMTP not configured; OTP could not be emailed."

  mail = MIMEText(
    f"Your portfolio access code is {otp}.\n\nThis one-time code expires in exactly 20 minutes. If you did not request it, you can ignore this email.",
    "plain"
  )
  mail["Subject"] = "Your portfolio access code"
  mail["From"] = sender
  mail["To"] = email

  try:
    with smtplib.SMTP(host, int(port)) as server:
      server.starttls()
      server.login(username, password)
      server.sendmail(sender, [email], mail.as_string())
    return True, "OTP sent."
  except Exception:
    return False, "OTP email failed."


@app.route("/")
def home():
    return {"status": "API is running"}

@app.route("/projects")
def demo_projects():
    return [
        {
            "id": 1,
            "title": "My Project",
            "description": "Test project"
        }
    ]

@app.route("/api/projects", methods=["GET"])
def api_get_projects():
  return jsonify({"projects": get_projects()}), 200

@app.route("/api/projects", methods=["POST"])
def api_create_project():
  payload = request.get_json(silent=True) or {}
  required = ["title", "description", "problem", "solution", "features", "tech_stack", "image_url", "live_url", "category"]
  for field in required:
    if not payload.get(field):
      return jsonify({"error": f"{field} is required"}), 400
  
  project = create_project(payload)
  return jsonify({"project": project}), 201

@app.route("/api/projects/<int:project_id>", methods=["GET"])
def api_get_project(project_id):
  project = get_project_by_id(project_id)
  if not project:
    return jsonify({"error": "Project not found"}), 404
  return jsonify({"project": project}), 200

@app.route("/api/projects/<int:project_id>", methods=["PUT"])
def api_update_project(project_id):
  payload = request.get_json(silent=True) or {}
  with get_connection() as conn:
    conn.execute(
      "UPDATE projects SET image_url = ? WHERE id = ?",
      (payload["image_url"], project_id)
    )
  return jsonify({"message": "Project updated"}), 200

@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def api_delete_project(project_id):
  with get_connection() as conn:
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
  return jsonify({"message": "Project deleted"}), 200

@app.route("/api/contact", methods=["POST"])
def api_contact():
  payload = request.get_json(silent=True) or {}
  name = payload.get("name", "").strip()
  email = payload.get("email", "").strip()
  message = payload.get("message", "").strip()

  if not name or not email or not message:
    return jsonify({"error": "name, email, and message are required"}), 400

  create_contact(name, email, message)
  email_sent, email_message = send_contact_email(name, email, message)
  response_message = "Message received and saved."
  if email_message:
    response_message = f"{response_message} {email_message}"

  return jsonify({"message": response_message, "email_sent": email_sent}), 201


@app.route("/api/auth/request-otp", methods=["POST"])
def api_request_otp():
  try:
    init_db()
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip().lower()
    recaptcha_token = payload.get("recaptchaToken", "")

    if not email or "@" not in email:
      return jsonify({"error": "A valid email address is required."}), 400

    verified, recaptcha_message = verify_recaptcha(recaptcha_token, "v3")
    if not verified:
      return jsonify({"error": recaptcha_message}), 400

    otp = f"{secrets.randbelow(1000000):06d}"
    expires_at = utc_now() + timedelta(minutes=OTP_TTL_MINUTES)

    with get_connection() as conn:
      conn.execute(
        """
        INSERT INTO login_otps (email, otp_hash, expires_at, request_ip, user_agent)
        VALUES (?, ?, ?, ?, ?)
        """,
        (email, hash_secret(otp), iso_time(expires_at), client_ip(), request.headers.get("User-Agent", ""))
      )

    sent, message = send_otp_email(email, otp)
    response = {
      "message": "If that email can receive access codes, a one-time password has been sent.",
      "expires_in_minutes": OTP_TTL_MINUTES,
      "email_sent": sent
    }

    if not sent and os.getenv("FLASK_ENV") == "development":
      response["dev_otp"] = otp
      response["debug_message"] = message

    if not sent:
      app.logger.warning("OTP email was not sent: %s", message)

    return jsonify(response), 200
  except Exception as error:
    app.logger.exception("OTP request failed")
    response = {"error": "Could not request one-time password."}
    if os.getenv("DEBUG_AUTH_ERRORS", "false").lower() == "true":
      response["detail"] = str(error)
      response["error_type"] = error.__class__.__name__
    return jsonify(response), 500


@app.route("/api/auth/verify-otp", methods=["POST"])
def api_verify_otp():
  payload = request.get_json(silent=True) or {}
  email = payload.get("email", "").strip().lower()
  otp = str(payload.get("otp", "")).strip()
  recaptcha_token = payload.get("recaptchaToken", "")

  if not email or not otp:
    return jsonify({"error": "Email and one-time password are required."}), 400

  verified, recaptcha_message = verify_recaptcha(recaptcha_token, "v2")
  if not verified:
    return jsonify({"error": recaptcha_message}), 400

  now = utc_now()
  with get_connection() as conn:
    row = conn.execute(
      """
      SELECT * FROM login_otps
      WHERE email = ? AND used_at IS NULL
      ORDER BY created_at DESC
      LIMIT 1
      """,
      (email,)
    ).fetchone()

    if not row:
      return jsonify({"error": "Invalid or expired one-time password."}), 401

    expires_at = datetime.fromisoformat(row["expires_at"])
    if now > expires_at or row["otp_hash"] != hash_secret(otp):
      return jsonify({"error": "Invalid or expired one-time password."}), 401

    session_token = secrets.token_urlsafe(32)
    session_expires_at = now + timedelta(minutes=SESSION_TTL_MINUTES)

    conn.execute("UPDATE login_otps SET used_at = ? WHERE id = ?", (iso_time(now), row["id"]))
    conn.execute(
      """
      INSERT INTO access_logs (email, session_token_hash, login_ip, user_agent, expires_at)
      VALUES (?, ?, ?, ?, ?)
      """,
      (
        email,
        hash_secret(session_token),
        client_ip(),
        request.headers.get("User-Agent", ""),
        iso_time(session_expires_at)
      )
    )

  return jsonify({
    "message": "Access granted.",
    "session_token": session_token,
    "expires_at": iso_time(session_expires_at)
  }), 200


@app.route("/api/auth/session", methods=["GET"])
def api_check_session():
  auth_header = request.headers.get("Authorization", "")
  token = auth_header.replace("Bearer ", "", 1).strip()
  if not token:
    return jsonify({"authenticated": False}), 401

  with get_connection() as conn:
    row = conn.execute(
      "SELECT email, expires_at FROM access_logs WHERE session_token_hash = ? ORDER BY login_at DESC LIMIT 1",
      (hash_secret(token),)
    ).fetchone()

  if not row or utc_now() > datetime.fromisoformat(row["expires_at"]):
    return jsonify({"authenticated": False}), 401

  return jsonify({"authenticated": True, "email": row["email"], "expires_at": row["expires_at"]}), 200


@app.route("/api/admin/access-logs", methods=["GET"])
def api_access_logs():
  admin_token = os.getenv("ADMIN_ACCESS_TOKEN")
  provided_token = request.headers.get("X-Admin-Token", "")
  if not admin_token or provided_token != admin_token:
    return jsonify({"error": "Unauthorized"}), 401

  with get_connection() as conn:
    rows = conn.execute(
      """
      SELECT id, email, login_ip, user_agent, login_at, expires_at
      FROM access_logs
      ORDER BY login_at DESC
      LIMIT 200
      """
    ).fetchall()

  return jsonify({"logs": [dict(row) for row in rows]}), 200


@app.route("/api/download-cv", methods=["GET"])
def api_download_cv():
  cv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cv", "resume.pdf")
  if not os.path.exists(cv_path):
    return jsonify({"error": "CV file not found"}), 404
  return send_file(cv_path, as_attachment=True, download_name="resume.pdf")


@app.errorhandler(404)
def not_found(_):
  return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_):
  return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
