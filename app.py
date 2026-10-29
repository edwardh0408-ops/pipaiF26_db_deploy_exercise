import csv
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent


@app.get("/")
def home():
    return send_from_directory(ROOT / "frontend", "index.html")


@app.get("/api/students")
def students():
    with (ROOT / "databases" / "student.csv").open(newline="", encoding="utf-8") as handle:
        return jsonify([row["full_name"] for row in csv.DictReader(handle)])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
