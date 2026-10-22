"""Connect to DATABASE_URL and run the intake sanity queries.

The lab SQL names tables students, student_tools, and tools. This database
uses student, student_tool, and tool, with full_name and tool_id.
"""

import psycopg2

from load_intake import ROOT, load_database_url

QUERIES = (
    """
    SELECT count(*) FROM student;
    """,
    """
    SELECT full_name, school_year FROM student LIMIT 5;
    """,
    """
    SELECT t.name, COUNT(*) AS n_students
    FROM student_tool st
    JOIN tool t ON st.tool_id = t.tool_id
    GROUP BY t.name
    ORDER BY n_students DESC;
    """,
)


def main() -> None:
    connection = psycopg2.connect(load_database_url(ROOT / ".env"))
    try:
        with connection:
            with connection.cursor() as cursor:
                for statement in QUERIES:
                    print(statement.strip())
                    print()
                    cursor.execute(statement)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    print("\t".join(columns))
                    for row in rows:
                        print("\t".join(str(value) for value in row))
                    print()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
