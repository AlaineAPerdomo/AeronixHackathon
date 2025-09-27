import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import uuid

app = Flask(__name__, static_folder='../public', static_url_path='')
CORS(app)

# Create directories if they don't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')
if not os.path.exists('public'):
    os.makedirs('public')

@app.route('/api/generate', methods=['POST'])
def generate_test_plan():
    if 'netlist' not in request.files:
        return jsonify({"error": "Netlist file is required."}), 400

    # --- File Handling ---
    netlist_file = request.files['netlist']
    bom_file = request.files.get('bom')
    layout_image_file = request.files.get('layout_image')
    
    # Use a unique filename to avoid conflicts
    run_id = str(uuid.uuid4())
    
    netlist_path = os.path.join('uploads', f"{run_id}_{netlist_file.filename}")
    netlist_file.save(netlist_path)

    command = [
        "python",
        "src/create_test_plan.py",
        "--netlist", netlist_path
    ]

    if bom_file:
        bom_path = os.path.join('uploads', f"{run_id}_{bom_file.filename}")
        bom_file.save(bom_path)
        command.extend(["--bom", bom_path])

    if layout_image_file:
        layout_image_path = os.path.join('uploads', f"{run_id}_{layout_image_file.filename}")
        layout_image_file.save(layout_image_path)
        command.extend(["--layout_image", layout_image_path])

    # --- Re-ingest Flag ---
    re_ingest = request.form.get('re_ingest') == 'true'
    if re_ingest:
        command.append("--re-ingest")

    # --- Output Path ---
    output_filename = f"Test_Plan_{run_id}.docx"
    output_path = os.path.join('public', output_filename)
    command.extend(["--output", output_path])

    # --- Execute Script ---
    try:
        print(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Script STDOUT:", result.stdout)
        
        return jsonify({
            "message": "Test plan generated successfully!",
            "downloadUrl": f"/{output_filename}"
        })

    except subprocess.CalledProcessError as e:
        print("Script STDERR:", e.stderr)
        return jsonify({
            "error": "Failed to generate test plan.",
            "details": e.stderr
        }), 500
    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../public', path)

if __name__ == '__main__':
    app.run(debug=True, port=5001)