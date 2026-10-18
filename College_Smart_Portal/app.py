
import os
import sqlite3
from pathlib import Path
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "college_portal.db"

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "change-this-secret-key-before-deployment"
)
app.config["DATABASE"] = str(DB_PATH)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

DEPARTMENTS = [
    "Computer Engineering",
    "Electronics Engineering",
    "Mechanical Engineering"
]


# ---------------- DATABASE ----------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(DB_PATH)

    db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            attendance REAL DEFAULT 0,
            marks REAL DEFAULT 0,
            email TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            student_name TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'In Progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            details TEXT NOT NULL,
            notice_date TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester TEXT NOT NULL
        );
    """)

    # Sample data is inserted only when each table is empty.
    if db.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        db.executemany("""
            INSERT INTO students
            (student_code, name, department, year,
             attendance, marks, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            ("CO101", "Pranjali Gursude",
             "Computer Engineering", "Final Year",
             92, 87, "pranjali@example.com"),
            ("EJ102", "Sneha Shinde",
             "Electronics Engineering", "Third Year",
             89, 84, "sneha@example.com"),
            ("ME103", "Priya Patil",
             "Mechanical Engineering", "Second Year",
             95, 91, "priya@example.com")
        ])

    if db.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
        db.executemany("""
            INSERT INTO projects
            (title, department, student_name, description, status)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (
                "College Smart Portal",
                "Computer Engineering",
                "Pranjali Gursude",
                "A web portal for student records, academic information, "
                "notices and feedback.",
                "Completed"
            ),
            (
                "AI Study Tips",
                "Computer Engineering",
                "Student Team",
                "An AI-assisted module that provides study guidance "
                "based on a student's topic.",
                "In Progress"
            )
        ])

    if db.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 0:
        db.executemany("""
            INSERT INTO notices (title, details, notice_date)
            VALUES (?, ?, ?)
        """, [
            (
                "Semester Examination",
                "Please check the department notice board "
                "for the final timetable.",
                "2026-11-10"
            ),
            (
                "Scholarship Form",
                "Eligible students should submit scholarship "
                "documents to the office.",
                "2026-11-15"
            ),
            (
                "Project Exhibition",
                "Final-year project teams should prepare "
                "their demonstrations.",
                "2026-11-20"
            )
        ])

    if db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 0:
        db.executemany("""
            INSERT INTO subjects
            (subject_code, subject_name, department, semester)
            VALUES (?, ?, ?, ?)
        """, [
            ("CS601", "Software Engineering",
             "Computer Engineering", "Semester 6"),
            ("CS602", "Computer Networks",
             "Computer Engineering", "Semester 6"),
            ("CS603", "Web-Based Application Development",
             "Computer Engineering", "Semester 6")
        ])

    db.commit()
    db.close()


# ---------------- ADMIN LOGIN ----------------

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in as administrator first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------- HOME AND ABOUT ----------------

@app.route("/")
def home():
    db = get_db()

    stats = {
        "students": db.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0],
        "projects": db.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0],
        "notices": db.execute(
            "SELECT COUNT(*) FROM notices"
        ).fetchone()[0],
        "feedback": db.execute(
            "SELECT COUNT(*) FROM feedback"
        ).fetchone()[0]
    }

    notices = db.execute("""
        SELECT * FROM notices
        ORDER BY id DESC LIMIT 3
    """).fetchall()

    return render_template(
        "home.html", stats=stats, notices=notices
    )


@app.route("/about")
def about():
    college = {
        "name": "Government Polytechnic Hingoli",
        "location": "Hingoli, Maharashtra",
        "established": "1985",
        "affiliation": "MSBTE",
        "departments": DEPARTMENTS
    }
    return render_template("about.html", college=college)


# ---------------- STUDENT MANAGEMENT ----------------

@app.route("/students")
def students():
    db = get_db()
    search = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 5

    conditions = []
    params = []

    if search:
        conditions.append(
            "(name LIKE ? OR student_code LIKE ? OR email LIKE ?)"
        )
        term = f"%{search}%"
        params.extend([term, term, term])

    if department:
        conditions.append("department = ?")
        params.append(department)

    where_clause = (
        " WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    total = db.execute(
        "SELECT COUNT(*) FROM students" + where_clause,
        params
    ).fetchone()[0]

    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)

    rows = db.execute("""
        SELECT * FROM students
    """ + where_clause + """
        ORDER BY id DESC LIMIT ? OFFSET ?
    """, params + [per_page, (page - 1) * per_page]).fetchall()

    departments = db.execute("""
        SELECT DISTINCT department FROM students
        ORDER BY department
    """).fetchall()

    return render_template(
        "students.html",
        students=rows,
        search=search,
        department=department,
        departments=departments,
        page=page,
        pages=pages,
        total=total
    )


def validate_student_form():
    code = request.form.get("student_code", "").strip()
    name = request.form.get("name", "").strip()
    department = request.form.get("department", "").strip()
    year = request.form.get("year", "").strip()
    email = request.form.get("email", "").strip()

    try:
        attendance = float(request.form.get("attendance", "0"))
        marks = float(request.form.get("marks", "0"))
    except ValueError:
        raise ValueError("Attendance and marks must be numeric.")

    if not all([code, name, department, year]):
        raise ValueError("Please fill in all required fields.")

    if not 0 <= attendance <= 100:
        raise ValueError("Attendance must be between 0 and 100.")

    if not 0 <= marks <= 100:
        raise ValueError("Marks must be between 0 and 100.")

    return (
        code, name, department, year,
        attendance, marks, email
    )


@app.route("/students/add", methods=["GET", "POST"])
@admin_required
def add_student():
    if request.method == "POST":
        try:
            values = validate_student_form()
            db = get_db()
            db.execute("""
                INSERT INTO students
                (student_code, name, department, year,
                 attendance, marks, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, values)
            db.commit()

            flash("Student added successfully.", "success")
            return redirect(url_for("students"))

        except sqlite3.IntegrityError:
            flash("That Student ID already exists.", "danger")
        except ValueError as error:
            flash(str(error), "danger")

    return render_template("student_form.html", student=None)


@app.route("/students/<int:student_id>/edit",
           methods=["GET", "POST"])
@admin_required
def edit_student(student_id):
    db = get_db()
    student = db.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if student is None:
        flash("Student record not found.", "danger")
        return redirect(url_for("students"))

    if request.method == "POST":
        try:
            values = validate_student_form()
            db.execute("""
                UPDATE students
                SET student_code=?, name=?, department=?, year=?,
                    attendance=?, marks=?, email=?
                WHERE id=?
            """, values + (student_id,))
            db.commit()

            flash("Student record updated.", "success")
            return redirect(url_for("students"))

        except sqlite3.IntegrityError:
            flash("That Student ID already exists.", "danger")
        except ValueError as error:
            flash(str(error), "danger")

    return render_template("student_form.html", student=student)


@app.route("/students/<int:student_id>/delete", methods=["POST"])
@admin_required
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    flash("Student record deleted.", "info")
    return redirect(url_for("students"))


# ---------------- ACADEMICS ----------------

@app.route("/academics")
def academics():
    subjects = get_db().execute("""
        SELECT * FROM subjects
        ORDER BY department, subject_code
    """).fetchall()

    return render_template("academics.html", subjects=subjects)


# ---------------- PROJECTS ----------------

@app.route("/projects")
def projects():
    rows = get_db().execute("""
        SELECT * FROM projects ORDER BY id DESC
    """).fetchall()

    return render_template("projects.html", projects=rows)


@app.route("/projects/add", methods=["GET", "POST"])
@admin_required
def add_project():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        department = request.form.get("department", "").strip()
        student_name = request.form.get("student_name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "In Progress").strip()

        if not all([title, department, student_name, description]):
            flash("Please complete all required fields.", "danger")
        else:
            db = get_db()
            db.execute("""
                INSERT INTO projects
                (title, department, student_name, description, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                title, department, student_name,
                description, status or "In Progress"
            ))
            db.commit()

            flash("Project added successfully.", "success")
            return redirect(url_for("projects"))

    return render_template("project_form.html")


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def delete_project(project_id):
    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("projects"))


# ---------------- NOTICES ----------------


@app.route("/notices")
def notices():
    db = get_db()

    rows = db.execute("""
        SELECT * FROM notices ORDER BY id DESC
    """).fetchall()

    return render_template("notices.html", notices=rows)


@app.route("/notices/add", methods=["GET", "POST"])
@admin_required
def add_notice():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        details = request.form.get("details", "").strip()
        notice_date = request.form.get("notice_date", "").strip()

        if not title or not details:
            flash("Title and details are required.", "danger")
            return render_template("notice_form.html")

        db = get_db()
        db.execute("""
            INSERT INTO notices (title, details, notice_date)
            VALUES (?, ?, ?)
        """, (title, details, notice_date or None))
        db.commit()

        flash("Notice published successfully!", "success")
        return redirect(url_for("notices"))

    return render_template("notice_form.html")


@app.route("/notices/delete/<int:notice_id>", methods=["POST"])
@admin_required
def delete_notice(notice_id):
    db = get_db()

    notice = db.execute("""
        SELECT id FROM notices WHERE id = ?
    """, (notice_id,)).fetchone()

    if notice is None:
        flash("Notice not found.", "danger")
    else:
        db.execute("""
            DELETE FROM notices WHERE id = ?
        """, (notice_id,))
        db.commit()

        flash("Notice deleted successfully!", "success")

    return redirect(url_for("notices"))



# ---------------- FEEDBACK ----------------

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    db = get_db()

    if request.method == "POST":
        name = request.form.get("student_name", "").strip()
        message = request.form.get("message", "").strip()

        try:
            rating = int(request.form.get("rating", "5"))
        except ValueError:
            rating = 0

        if not name or not message or rating not in range(1, 6):
            flash(
                "Enter your name, message and rating from 1 to 5.",
                "danger"
            )
        else:
            db.execute("""
                INSERT INTO feedback (student_name, rating, message)
                VALUES (?, ?, ?)
            """, (name, rating, message))
            db.commit()

            flash("Thank you! Your feedback has been submitted.", "success")
            return redirect(url_for("feedback"))

    feedbacks = db.execute("""
        SELECT * FROM feedback ORDER BY id DESC LIMIT 10
    """).fetchall()

    return render_template("feedback.html", feedbacks=feedbacks)


# ---------------- ADMISSION INFORMATION ----------------

@app.route("/admission")
def admission():
    return render_template("admission.html")


# ---------------- AI STUDY TIPS ----------------

@app.route("/study-tips", methods=["GET", "POST"])
def study_tips():
    answer = None
    topic = ""

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        api_key = os.getenv("GROQ_API_KEY", "").strip()

        if not topic:
            flash("Enter a subject or topic first.", "warning")

        elif not api_key or api_key == "your_groq_api_key_here":
            answer = (
                "AI is not connected yet. Add your Groq API key to the "
                ".env file to enable AI tips. Meanwhile, divide the topic "
                "into small sections, revise definitions, solve practice "
                "questions and explain the topic in your own words."
            )

        else:
            try:
                from groq import Groq

                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model=os.getenv(
                        "GROQ_MODEL", "llama-3.3-70b-versatile"
                    ),
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a friendly diploma-college study "
                                "coach. Give practical study tips in "
                                "simple English."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Give a simple study plan and revision "
                                f"tips for: {topic}"
                            )
                        }
                    ],
                    temperature=0.5,
                    max_tokens=500
                )

                answer = response.choices[0].message.content

            except Exception as error:
                app.logger.exception("Study tips AI request failed")
                answer = (
                    "The AI service could not respond. Check the .env "
                    "settings, internet connection and model availability. "
                    "You can still study by revising definitions, making "
                    "short notes and solving practice questions."
                )

    return render_template(
        "study_tips.html", answer=answer, topic=topic
    )


# ---------------- LOGIN / LOGOUT ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["admin_logged_in"] = True
            flash("Welcome, administrator.", "success")
            return redirect(url_for("home"))

        flash("Incorrect username or password.", "danger")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ---------------- ERROR PAGE ----------------

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# Create database tables and sample data on startup.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
