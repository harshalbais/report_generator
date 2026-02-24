from flask import Flask, request, send_file, jsonify
import os
import json
import shutil
import re
from datetime import datetime
from report import generate_report_from_json
import pikepdf
from email.message import EmailMessage
import smtplib


# ==========================================
# PDF Compression
# ==========================================
def compress_pdf(input_path, output_path):
    try:
        with pikepdf.open(input_path) as pdf:
            pdf.save(
                output_path,
                optimize_streams=True,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate
            )
        print("✅ PDF compressed successfully")
    except Exception as e:
        print("❌ Compression failed:", str(e))


# ==========================================
# Email Function
# ==========================================
def send_status_email(subject, body, attachment_path=None):

    recipients = [
        "codequestcrew@gmail.com",
        "hbphysics332@gmail.com"
    ]

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = os.environ.get("EMAIL_USER")
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=os.path.basename(attachment_path)
                )

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(
            os.environ.get("EMAIL_USER"),
            os.environ.get("EMAIL_PASS")
        )
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email failed:", str(e))


# ==========================================
# Flask App
# ==========================================
app = Flask(__name__)

TEMP_FOLDER = "temp_reports"
REPORT_FOLDER = "reports"

os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return "Drone Report API Running 🚀"


# ==========================================
# Upload JSON Endpoint
# ==========================================
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


# ==========================================
# Generate Report Endpoint
# ==========================================
@app.route("/generate-report", methods=["POST"])
def generate_report():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        video_link = data.get("video_link")

        if not video_link:
            return jsonify({"error": "Video link required"}), 400

        # -----------------------------------
        # Collect JSON files
        # -----------------------------------
        json_files = [f for f in os.listdir(TEMP_FOLDER) if f.endswith(".json")]

        if not json_files:
            return jsonify({"error": "No JSON files found"}), 400

        # -----------------------------------
        # Combine Data
        # -----------------------------------
        combined_data = {
            "location": "Combined Site Report",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "drone_id": "",
            "video_link": video_link,
            "violations": []
        }

        first_drone_id = None

        for i, file in enumerate(json_files):
            file_path = os.path.join(TEMP_FOLDER, file)

            with open(file_path, "r") as f:
                file_data = json.load(f)

            if i == 0:
                first_drone_id = file_data.get("drone_id", "Drone_Report")

            combined_data["violations"].extend(file_data.get("violations", []))

        # -----------------------------------
        # Clean Drone ID
        # -----------------------------------
        cleaned_name = re.sub(r'_\d+$', '', first_drone_id or "Drone_Report")
        cleaned_name = cleaned_name.replace("_", " ").upper().replace(" ", "_")

        combined_data["drone_id"] = cleaned_name

        # -----------------------------------
        # Generate PDF
        # -----------------------------------
        output_filename = f"{cleaned_name}.pdf"
        output_path = os.path.join(REPORT_FOLDER, output_filename)

        generate_report_from_json(combined_data, output_path)

        print("✅ Report generated:", output_path)

        # -----------------------------------
        # Compress PDF
        # -----------------------------------
        compressed_path = output_path.replace(".pdf", "_COMPRESSED.pdf")

        compress_pdf(output_path, compressed_path)

        # Replace with compressed version
        output_path = compressed_path
        output_filename = os.path.basename(output_path)

        print("✅ Using compressed report:", output_path)

        # -----------------------------------
        # Send Email
        # -----------------------------------
        send_status_email(
            subject="✅ Drone Report Generated Successfully",
            body=f"""
Report Status: SUCCESS

Drone ID: {cleaned_name}
Total Violations: {len(combined_data['violations'])}
Video Link: {video_link}
""",
            attachment_path=output_path
        )

        # -----------------------------------
        # Cleanup JSON files
        # -----------------------------------
        shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        # -----------------------------------
        # Return File
        # -----------------------------------
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        print("❌ Report generation error:", str(e))
        return jsonify({"error": str(e)}), 500
