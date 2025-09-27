from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, subprocess

app = Flask(__name__)
CORS(app, resources={r"/upload": {"origins": "http://localhost:5173"}})

@app.route("/outputs/final.docx", methods=["GET"])
def download_file():
    return send_from_directory("./outputs", "final.docx", as_attachment=True)

@app.route("/upload", methods=["POST"])
def upload():
    netlist = request.files.get("netlist")
    csv_file = request.files.get("csv")

    if not netlist or not csv_file:
        return jsonify({"message": "Missing files"}), 400

    UPLOAD_DIR = "./uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    netlist_path = os.path.join(UPLOAD_DIR, netlist.filename)
    csv_path = os.path.join(UPLOAD_DIR, csv_file.filename)
    netlist.save(netlist_path)
    csv_file.save(csv_path)

    result = subprocess.run(
        ["python", "backend/process_script.py", netlist_path, csv_path],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return jsonify({"message": "Processing complete", "output": result.stdout})
    else:
        return jsonify({"message": "Processing failed", "error": result.stderr}), 500

if __name__ == '__main__':
    app.run(debug=True)


