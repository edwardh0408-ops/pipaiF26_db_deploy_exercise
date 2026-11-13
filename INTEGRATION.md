# Group assignment integration

Hand this file to an agent working in the app repo. That agent does not have the model repo. The two Python files named below are the whole model. Copy them in and follow these steps. Do not edit them to fit the app. The app adapts to them.

The deployed process is `app.py` (Flask, started by gunicorn). The schema and the loader are both in `load_intake.py`: the schema is the `DDL` string, and `main` loads the wide CSV into Postgres. There is no separate SQL file.

## 1. What these two files do

`cluster_model.py` stores three centroids and `predict_cluster` returns the label of the nearest centroid for four skill ratings. `assignment_rules.py` labels each student with that function, orders the clusters from most students to fewest, sorts each cluster by `id`, and deals that list round-robin into groups. The app reads Postgres, calls `assign_groups`, and builds the HTTP response; it leaves both files as they are.

## 2. Files to copy

Copy these two files into the app repository root, the directory that contains `app.py`:

- `cluster_model.py`
- `assignment_rules.py`

Leave both files byte for byte. `assignment_rules.py` imports `cluster_model` by that top-level name, which resolves when the two files sit on the app's Python path next to `app.py`.

Do not copy anything else from the model repo. Do not call `load_students` or `main` in `assignment_rules.py`. Those read a wide CSV that is not part of the app.

## 3. The two functions

`predict_cluster(skills)` takes one sequence of four numbers, in this order: programming, data and stats, frontend design, business pitch. It returns an int cluster label, `0`, `1`, or `2`. On a distance tie it keeps the earlier centroid.

```python
predict_cluster([3, 3, 1, 2])  # 1
```

`assign_groups(students, n_groups=8)` takes the whole class and how many groups to deal. Each student is a dict with `id` (string) and `skills` (those four numbers). It returns a list in the same order as the input. Each item is `id`, `cluster`, and `group`. Groups are numbered from 1.

```python
assign_groups(
    [
        {"id": "a", "skills": [3, 3, 3, 4]},
        {"id": "c", "skills": [4, 5, 4, 5]},
        {"id": "b", "skills": [3, 4, 1, 2]},
    ],
    n_groups=2,
)
# [
#   {"id": "a", "cluster": 0, "group": 1},
#   {"id": "c", "cluster": 2, "group": 1},
#   {"id": "b", "cluster": 1, "group": 2},
# ]
```

That return value is for the server to aggregate. It is not the HTTP body. The route in section 5 must not send any one person's cluster.

## 4. Where the data comes from

The centroids were fit on a wide CSV, one row per student. The app's data is the Postgres database created and filled by `load_intake.py`. Build one dict per student and pass that list to `assign_groups`. Use `n_groups=8`. That number is not stored in the database.

| What the model expects | Wide CSV | Postgres |
| --- | --- | --- |
| `id` | column `netid` | `student.submitted_id` |
| `skills[0]` | column `skill_programming` | `student_skill.rating` where `skill.code = 'programming'` |
| `skills[1]` | column `skill_data_stats` | `student_skill.rating` where `skill.code = 'data_stats'` |
| `skills[2]` | column `skill_frontend_design` | `student_skill.rating` where `skill.code = 'frontend_design'` |
| `skills[3]` | column `skill_business_pitch` | `student_skill.rating` where `skill.code = 'business_pitch'` |

`student.submitted_id` is the `netid` value. Pass it through as `id`. `student.student_id` is a generated integer; use it only to join `student_skill`. `student.id_kind` is `netid`, `n_number`, or `email`. The CSV column was still named `netid` for all three, so include every student, including N-numbers and emails.

The four ratings are columns on the CSV and rows in Postgres. `skill.code` drops the `skill_` prefix. The loader inserts `skill_id` 1 through 4 in the same order as the skill list above, and inserts one `student_skill` row per skill with `rating` from 1 to 5. Assemble `skills` in the order in the table, as numbers. The database has no cluster column. The CSV does, from the original fit. Cluster comes only from `predict_cluster`.

The response needs display names. Those are `student.full_name`, which was the CSV column `name`. Do not pass the name into either function.

```sql
SELECT s.submitted_id, s.full_name, sk.code, ss.rating
FROM student AS s
JOIN student_skill AS ss ON ss.student_id = s.student_id
JOIN skill AS sk ON sk.skill_id = ss.skill_id;
```

## 5. Backend

Add `GET /api/groups` to `app.py`. That is the process gunicorn runs. Leave `GET /api/students` as it is. It returns a list of name strings from a CSV, and the current page depends on that.

Connect with `psycopg2` and `DATABASE_URL`, the same URL `load_intake.py` reads from `.env`. `requirements.txt` currently lists only `flask` and `gunicorn`. Add `psycopg2-binary` so the slim image can install the driver the loader imports.

Read every student with the query in section 4. Build the `assign_groups` input, call `assign_groups(students)` so `n_groups` stays 8, then discard the per-person cluster on the way out. Take each group's centroid from `cluster_model.CENTROIDS` (label 0, then 1, then 2). Do not recompute them.

Return one JSON object:

- `n_groups`: `8`.
- `groups`: one object per group, groups 1 through 8, in that order. Each has `group` (int), `members` (list of `full_name` strings only, sorted by `submitted_id`), and `cluster_counts` (object with keys `"0"`, `"1"`, and `"2"`, including zeros).
- `clusters`: one object per centroid, in label order. Each has `cluster` (int), `students` (how many students got that label, an int), and `centroid` (the four numbers from `CENTROIDS`, same skill order as section 3).
- `groups_missing_a_cluster`: how many groups have a zero in `cluster_counts`.

`members` is names. There is no per-person cluster, id, or skill list anywhere in this JSON.

`cluster_counts` for a group of three people might be `{"0": 2, "1": 1, "2": 0}`. That does not say which person is which.

## 6. Frontend

Do not change the frontend in this step.

`GET /api/groups` returns the object in section 5. A later page can render `groups` as eight lists: the heading is `group`, the people are `members`, and `cluster_counts` is the mix of clusters in that group. `clusters` describes the three centroids: `students` is the size of that cluster, and `centroid` is four ratings in the order programming, data and stats, frontend design, business pitch. `groups_missing_a_cluster` is a single count of groups that lack at least one cluster. `n_groups` is the number of groups dealt.

The payload has no field that attaches a cluster to a named person. A page should not invent one.

## 7. Packaging

`Dockerfile` copies `app.py`, `frontend/`, and `databases/`. It does not copy the model modules. Add:

```dockerfile
COPY cluster_model.py assignment_rules.py .
```

Those two paths are the image workdir `/app`, which is where `app:app` is loaded, so `import cluster_model` and `import assignment_rules` work unchanged.

The model files use only the standard library. They add nothing to `requirements.txt`. The Postgres driver in section 5 is the dependency the route adds.

## 8. Test

Load the database with `load_intake.py`, then start the app (`python app.py`, port 8000 unless `PORT` is set):

```bash
curl -s http://127.0.0.1:8000/api/groups
```

On this class, that response has `n_groups` of 8 and `groups_missing_a_cluster` of 6. Member counts are 3 for groups 1 through 7, and 2 for group 8. `cluster_counts` from the same run:

| group | members | `"0"` | `"1"` | `"2"` |
| --- | --- | --- | --- | --- |
| 1 | 3 | 2 | 1 | 0 |
| 2 | 3 | 2 | 1 | 0 |
| 3 | 3 | 2 | 0 | 1 |
| 4 | 3 | 2 | 0 | 1 |
| 5 | 3 | 2 | 0 | 1 |
| 6 | 3 | 1 | 1 | 1 |
| 7 | 3 | 1 | 1 | 1 |
| 8 | 2 | 1 | 1 | 0 |

`clusters[].students` is 13 for cluster 0, 5 for cluster 1, and 5 for cluster 2. Groups 6 and 7 are the two groups that contain every cluster.
