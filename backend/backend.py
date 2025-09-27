from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow React frontend

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    file.save(f"./uploads/{file.filename}")
    return jsonify({'message': f"{file.filename} uploaded successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
