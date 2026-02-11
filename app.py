from flask import Flask, request, send_file, jsonify
import os
from report import generate_report_from_json

app = Flask(__name__)

@app.route("/")
def home():
    return "Drone Report API Running 🚀"

@app.route("/generate-report", methods=["GET", "POST"])
def generate_report():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        output_path = "generated_report.pdf"

        generate_report_from_json(data, output_path)

        return send_file(
            output_path,
            as_attachment=True,
            download_name="Drone_Report.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
