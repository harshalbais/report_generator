from flask import Flask, request, send_file, jsonify
import os
import json
import shutil
from report import generate_report_from_json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


def send_status_email(subject, body, attachment_path=None):
    try:
        sender_email = os.environ.get("EMAIL_USER")
        sender_password = os.environ.get("EMAIL_PASS")

        # 🔥 Multiple recipients (comma separated in ENV)
        receiver_emails = os.environ.get("EMAIL_RECEIVERS", "")
        receiver_list = [email.strip() for email in receiver_emails.split(",") if email.strip()]

        if not receiver_list:
            print("❌ No receiver emails configured")
            return

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = ", ".join(receiver_list)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # 🔥 Attach PDF if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_list, msg.as_string())
        server.quit()

        print("✅ Email sent to multiple recipients")

    except Exception as e:
        print("❌ Email failed:", e)


app = Flask(__name__)

TEMP_FOLDER = "temp_reports"
os.makedirs(TEMP_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return "Drone Report API Running 🚀"


@app.route("/upload-json", methods=["POST"])
def upload_json():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        file_count = len(os.listdir(TEMP_FOLDER)) + 1
        file_path = os.path.join(TEMP_FOLDER, f"report_{file_count}.json")

        with open(file_path, "w") as f:
            json.dump(data, f)

        return jsonify({"message": "JSON stored in backend"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/generate-report", methods=["POST"])
def generate_report():
    try:
        video_link = request.json.get("video_link")

        if not video_link:
            send_status_email(
                subject="❌ Drone Report Failed",
                body="Video link was not provided."
            )
            return jsonify({"error": "Video link required"}), 400

        json_files = [f for f in os.listdir(TEMP_FOLDER) if f.endswith(".json")]

        if not json_files:
            send_status_email(
                subject="❌ Drone Report Failed",
                body="No JSON files found in backend."
            )
            return jsonify({"error": "No JSON files found"}), 400

        combined_data = {
            "location": "Combined Site Report",
            "date": "2026-02-11",
            "drone_id": "",
            "video_link": video_link,
            "violations": []
        }

        first_drone_id = None

        for i, file in enumerate(json_files):
            with open(os.path.join(TEMP_FOLDER, file)) as f:
                data = json.load(f)

                if i == 0:
                    first_drone_id = data.get("drone_id", "Drone_Report")

                if "violations" in data:
                    combined_data["violations"].extend(data["violations"])

        import re
        if first_drone_id:
            cleaned_name = re.sub(r'_\d+$', '', first_drone_id)
        else:
            cleaned_name = "Drone_Report"

        cleaned_name = cleaned_name.replace("_", " ").title().replace(" ", "_")

        combined_data["drone_id"] = cleaned_name
        output_path = f"{cleaned_name}.pdf"

        generate_report_from_json(combined_data, output_path)

        # ✅ SEND SUCCESS EMAIL BEFORE RETURN
        send_status_email(
            subject="✅ Drone Report Generated Successfully",
            body=f"""
Report Status: SUCCESS

Drone ID: {cleaned_name}
Total Violations: {len(combined_data['violations'])}
Video Link: {video_link}

The report has been generated successfully.
""",
            attachment_path=output_path
        )

        # Cleanup
        shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{cleaned_name}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:

        # ❌ SEND FAILURE EMAIL
        send_status_email(
            subject="❌ Drone Report Generation Failed",
            body=f"""
Report Status: FAILED

Error:
{str(e)}
"""
        )

        return jsonify({"error": str(e)}), 500
