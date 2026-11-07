
from flask import Flask, render_template, request, redirect
from datetime import date
import sqlite3

from database import init_db, DATABASE_PATH

app = Flask(__name__)

# Initialize the SQLite database
init_db()


# Get all assignments from the database
def get_assignments():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    assignments = connection.execute(
        "SELECT * FROM assignments ORDER BY id DESC"
    ).fetchall()

    connection.close()
    return assignments


# Home page
@app.route("/")
def home():
    return render_template("index.html")




# View and add assignments
@app.route("/assignments", methods=["GET", "POST"])
def assignments():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if title and subject and due_date:
            connection = sqlite3.connect(DATABASE_PATH)

            connection.execute(
                """
                INSERT INTO assignments (title, subject, due_date)
                VALUES (?, ?, ?)
                """,
                (title, subject, due_date)
            )

            connection.commit()
            connection.close()

        return redirect("/assignments")

    all_assignments = get_assignments()

    total_assignments = len(all_assignments)

    completed_count = sum(
        1 for assignment in all_assignments
        if assignment["completed"] == 1
    )

    pending_count = total_assignments - completed_count

    # Get the selected filter
    selected_status = request.args.get("status", "all")

    # Filter assignments
    if selected_status == "completed":
        displayed_assignments = [
            a for a in all_assignments if a["completed"] == 1
        ]

    elif selected_status == "pending":
        displayed_assignments = [
            a for a in all_assignments if a["completed"] == 0
        ]

    else:
        displayed_assignments = all_assignments

    # Get selected sorting option
    selected_sort = request.args.get("sort", "newest")

    # Sort assignments by due date
    if selected_sort == "earliest":
        displayed_assignments = sorted(
            displayed_assignments,
            key=lambda a: a["due_date"]
        )

    elif selected_sort == "latest":
        displayed_assignments = sorted(
            displayed_assignments,
            key=lambda a: a["due_date"],
            reverse=True
        )

    return render_template(
        "assignments.html",
        assignments=displayed_assignments,
        total_assignments=total_assignments,
        completed_count=completed_count,
        pending_count=pending_count,
        selected_status=selected_status,
        selected_sort=selected_sort
    )


# Delete an assignment
@app.route("/delete_assignment/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute(
        "DELETE FROM assignments WHERE id = ?",
        (assignment_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/assignments")


# Mark an assignment as completed or pending
@app.route("/toggle_complete/<int:assignment_id>", methods=["POST"])
def toggle_complete(assignment_id):
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute(
        """
        UPDATE assignments
        SET completed = CASE
            WHEN completed = 0 THEN 1
            ELSE 0
        END
        WHERE id = ?
        """,
        (assignment_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/assignments")



# Track assignment deadlines
@app.route("/deadlines")
def deadlines():
    today = date.today()
    all_assignments = get_assignments()
    deadline_assignments = []

    for assignment in all_assignments:
        assignment_dict = dict(assignment)
        due_date = date.fromisoformat(assignment_dict["due_date"])

        if assignment_dict["completed"] == 1:
            status = "Completed"

        elif due_date < today:
            status = "Overdue"

        elif due_date == today:
            status = "Due Today"

        else:
            status = "Upcoming"

        assignment_dict["status"] = status
        deadline_assignments.append(assignment_dict)

    return render_template(
        "deadlines.html",
        assignments=deadline_assignments
    )


# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
