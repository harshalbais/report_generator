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

# ======================================================
# CONFIG
# ======================================================

TEMP_FOLDER = "temp_reports"
REPORT_FOLDER = "reports"

os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

app = Flask(__name__)

# ======================================================
# SAFE PDF COMPRESSION (OVERWRITE SAME FILE)
# ======================================================

def compress_pdf(input_path):
    try:
        with pikepdf.open(input_path, allow_overwriting_input=True) as pdf:
            pdf.save(
                input_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate
            )

        print("✅ PDF compressed successfully")
        return True

    except Exception as e:
        print("⚠ Compression skipped:", str(e))
        return False

# ======================================================
# SAFE EMAIL FUNCTION (OPTIONAL)
# ======================================================

def send_status_email(subject, body, attachment_path=None):
    print("vo actually ye service temporily close h tho email sent nahi hoga  ")

# ======================================================
# ROUTES
# ======================================================

@app.route("/")
def home():
    return "🚀 Drone Report API Running"

# ======================================================
# UPLOAD JSON
# ======================================================

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

        return jsonify({"message": "JSON stored successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======================================================
# GENERATE REPORT
# ======================================================

@app.route("/generate-report", methods=["POST"])
def generate_report():

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        video_link = data.get("video_link")

        if not video_link:
            return jsonify({"error": "Video link required"}), 400

        json_files = [f for f in os.listdir(TEMP_FOLDER) if f.endswith(".json")]

        if not json_files:
            return jsonify({"error": "No JSON files found"}), 400

        # -----------------------------
        # Combine JSON Data
        # -----------------------------
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

            combined_data["violations"].extend(
                file_data.get("violations", [])
            )

        # -----------------------------
        # Clean Drone ID
        # -----------------------------
        cleaned_name = re.sub(r'_\d+$', '', first_drone_id or "Drone_Report")
        cleaned_name = cleaned_name.replace("_", " ").upper().replace(" ", "_")
        combined_data["drone_id"] = cleaned_name

        # -----------------------------
        # Generate PDF
        # -----------------------------
        output_filename = f"{cleaned_name}.pdf"
        output_path = os.path.join(REPORT_FOLDER, output_filename)

        generate_report_from_json(combined_data, output_path)

        print("✅ Report generated:", output_path)

        # -----------------------------
        # Compress (Overwrite Same File)
        # -----------------------------
        if compress_pdf(output_path):
            print("✅ Using compressed report")
        else:
            print("⚠ Using original PDF")

        # -----------------------------
        # Send Email (Optional)
        # -----------------------------
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

        # -----------------------------
        # Cleanup JSON files
        # -----------------------------
        shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        # -----------------------------
        # Return PDF
        # -----------------------------
        return send_file(
            os.path.abspath(output_path),
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        print("❌ Report generation error:", str(e))
        return jsonify({"error": str(e)}), 500

# ======================================================
# RUN SERVER
# ======================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
