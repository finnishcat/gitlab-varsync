from flask import Flask, jsonify, send_file, send_from_directory
from core import (
    export_variables_all_groups,
    write_new_variables,
    update_existing_variables,
    search_variable
)
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="/")


@app.route("/api/read")
def read():
    export_variables_all_groups()
    return send_excel()


@app.route("/api/write")
def write():
    write_new_variables()
    return send_excel()


@app.route("/api/update")
def update():
    update_existing_variables()
    return send_excel()


@app.route("/api/search")
def search():
    search_variable("SONAR_TOKEN")  # puoi adattare per prendere parametri
    return send_excel("SONAR_TOKEN.xlsx")


@app.route("/api/download")
def download():
    return send_excel()


@app.route("/api/license")
def license():
    with open("license.txt", "r") as f:
        return f.read()


def send_excel(filename="gitlab_variables_all_groups.xlsx"):
    if os.path.exists(filename):
        return send_file(filename, as_attachment=False)
    return jsonify({"error": "File not found"}), 404


# Serve frontend static files
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
