from flask import Flask, request, send_file, jsonify
import os
import json
import shutil
from report import generate_report_from_json

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



# ✅ 2️⃣ Generate Final Report (Auto Combine + Video Link)
@app.route("/generate-report", methods=["POST"])
def generate_report():
    try:
        video_link = request.json.get("video_link")

        if not video_link:
            return jsonify({"error": "Video link required"}), 400

        combined_data = {
            "location": "Combined Site Report",
            "date": "2026-02-11",
            "drone_id": "MULTI",
            "video_link": video_link,
            "violations": []
        }

        json_files = [f for f in os.listdir(TEMP_FOLDER) if f.endswith(".json")]

        if not json_files:
            return jsonify({"error": "No JSON files found"}), 400

        # 🔥 Combine all JSON files
        for file in json_files:
            with open(os.path.join(TEMP_FOLDER, file)) as f:
                data = json.load(f)
                if "violations" in data:
                    combined_data["violations"].extend(data["violations"])

        output_path = "final_report.pdf"
        generate_report_from_json(combined_data, output_path)

        # 🔥 Cleanup after generation
        shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        return send_file(
            output_path,
            as_attachment=True,
            download_name="Final_Report.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500




