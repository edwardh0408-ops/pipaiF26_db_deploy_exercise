import csv
import os
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, request, send_from_directory

from assignment_rules import assign_groups
from cluster_model import CENTROIDS

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent
DIST = ROOT / "frontend" / "dist"
SKILL_ORDER = (
    "programming",
    "data_stats",
    "frontend_design",
    "business_pitch",
)
N_GROUPS = 8


def database_url() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith(("postgres://", "postgresql://")):
            return line.strip('"').strip("'")
    raise RuntimeError("DATABASE_URL not found in .env")


@app.get("/")
def home():
    return send_from_directory(DIST, "index.html")


@app.get("/assets/<path:filename>")
def frontend_assets(filename):
    return send_from_directory(DIST / "assets", filename)


@app.get("/api/students")
def students():
    with (ROOT / "databases" / "student.csv").open(newline="", encoding="utf-8") as handle:
        return jsonify([row["full_name"] for row in csv.DictReader(handle)])


def class_rows():
    connection = psycopg2.connect(database_url())
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.submitted_id, s.full_name, sk.code, ss.rating
                FROM student AS s
                JOIN student_skill AS ss ON ss.student_id = s.student_id
                JOIN skill AS sk ON sk.skill_id = ss.skill_id
                """
            )
            return cursor.fetchall()
    finally:
        connection.close()


def requested_group_count():
    raw = request.args.get("n_groups")
    if raw is None or raw == "":
        return N_GROUPS
    try:
        count = int(raw)
    except ValueError:
        return None
    if count < 1:
        return None
    return count


@app.get("/api/groups")
def groups():
    n_groups = requested_group_count()
    if n_groups is None:
        return jsonify({"error": "n_groups must be a positive integer"}), 400

    by_id = {}
    for submitted_id, full_name, code, rating in class_rows():
        student = by_id.setdefault(
            submitted_id,
            {"id": submitted_id, "full_name": full_name, "ratings": {}},
        )
        student["ratings"][code] = rating

    model_input = [
        {
            "id": submitted_id,
            "skills": [student["ratings"][code] for code in SKILL_ORDER],
        }
        for submitted_id, student in by_id.items()
    ]
    assigned = assign_groups(model_input, n_groups)
    names = {submitted_id: student["full_name"] for submitted_id, student in by_id.items()}

    grouped = {group: [] for group in range(1, n_groups + 1)}
    cluster_sizes = {label: 0 for label in range(len(CENTROIDS))}
    for student in assigned:
        grouped[student["group"]].append(student)
        cluster_sizes[student["cluster"]] += 1

    groups_payload = []
    missing = 0
    for group in range(1, n_groups + 1):
        members = sorted(grouped[group], key=lambda student: student["id"])
        counts = {str(label): 0 for label in range(len(CENTROIDS))}
        for student in members:
            counts[str(student["cluster"])] += 1
        if any(count == 0 for count in counts.values()):
            missing += 1
        groups_payload.append(
            {
                "group": group,
                "members": [names[student["id"]] for student in members],
                "cluster_counts": counts,
            }
        )

    return jsonify(
        {
            "n_groups": n_groups,
            "groups": groups_payload,
            "clusters": [
                {
                    "cluster": label,
                    "students": cluster_sizes[label],
                    "centroid": list(centroid),
                }
                for label, centroid in enumerate(CENTROIDS)
            ],
            "groups_missing_a_cluster": missing,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
