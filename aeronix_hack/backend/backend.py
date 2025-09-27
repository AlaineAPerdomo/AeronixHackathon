from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/upload": {"origins": "http://localhost:5173"}})

@app.route("/upload", methods=["POST"])
def upload():
    netlist = request.files.get("netlist")
    csv_file = request.files.get("csv")

    print(netlist, csv_file)

    if not netlist or not csv_file:
        return jsonify({"message": "Missing files"}), 400


    netlist.save(f"./uploads/{netlist.filename}")
    csv_file.save(f"./uploads/{csv_file.filename}")

    return jsonify({"message": "Files uploaded successfully!"})

if __name__ == '__main__':
    app.run(debug=True)


