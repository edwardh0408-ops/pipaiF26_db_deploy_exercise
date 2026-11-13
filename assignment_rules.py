"""Assign students to groups by dealing cluster lists round-robin."""

import csv
from pathlib import Path

from cluster_model import predict_cluster

SKILL_COLUMNS = (
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
)
DATA_PATH = Path(__file__).resolve().parent / "class_dataset.csv"


def assign_groups(students, n_groups=8):
    labeled = [
        {"id": student["id"], "cluster": predict_cluster(student["skills"])}
        for student in students
    ]
    by_cluster = {}
    for student in labeled:
        by_cluster.setdefault(student["cluster"], []).append(student)

    ordered_clusters = sorted(by_cluster, key=lambda cluster: (-len(by_cluster[cluster]), cluster))
    deal = []
    for cluster in ordered_clusters:
        members = sorted(by_cluster[cluster], key=lambda student: student["id"])
        deal.extend(members)

    group_by_id = {
        student["id"]: (index % n_groups) + 1 for index, student in enumerate(deal)
    }
    return [
        {
            "id": student["id"],
            "cluster": student["cluster"],
            "group": group_by_id[student["id"]],
        }
        for student in labeled
    ]


def load_students(path):
    with path.open(newline="") as handle:
        return [
            {
                "id": row["netid"],
                "skills": [float(row[column]) for column in SKILL_COLUMNS],
            }
            for row in csv.DictReader(handle)
        ]


def main():
    assignments = assign_groups(load_students(DATA_PATH))
    clusters = sorted({student["cluster"] for student in assignments})
    groups = {}
    for student in assignments:
        groups.setdefault(student["group"], []).append(student)

    missing = 0
    for group in range(1, max(groups) + 1):
        members = groups.get(group, [])
        counts = {cluster: 0 for cluster in clusters}
        for student in members:
            counts[student["cluster"]] += 1
        breakdown = ", ".join(f"cluster {cluster}: {counts[cluster]}" for cluster in clusters)
        print(f"group {group}: {len(members)} students, {breakdown}")
        if any(count == 0 for count in counts.values()):
            missing += 1
    print(f"groups missing a cluster: {missing}")


if __name__ == "__main__":
    main()
