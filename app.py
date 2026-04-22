import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from database import init_db
from models import create_contact, get_project_by_id, get_projects
from seed import seed_projects_if_empty


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGIN", "*")}})
init_db()
seed_projects_if_empty()


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


@app.route("/api/projects", methods=["GET"])
def api_get_projects():
  return jsonify({"projects": get_projects()}), 200


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def api_get_project(project_id):
  project = get_project_by_id(project_id)
  if not project:
    return jsonify({"error": "Project not found"}), 404
  return jsonify({"project": project}), 200


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
