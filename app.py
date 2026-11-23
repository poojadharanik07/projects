
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import create_tables, get_connection

app = Flask(__name__)

# Session security key
app.secret_key = "smart-study-planner-development-key"

# Create database tables
create_tables()


@app.route("/")
def home():
    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO students (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash)
            )

            connection.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))

        except Exception as error:
            if "UNIQUE constraint failed" in str(error):
                flash("This email is already registered.")
            else:
                app.logger.exception("Registration failed")
                flash("Registration failed. Please try again.")

            return redirect(url_for("register"))

        finally:
            connection.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_connection()

        try:
            student = connection.execute(
                "SELECT * FROM students WHERE email = ?",
                (email,)
            ).fetchone()
        finally:
            connection.close()

        if student and check_password_hash(
            student["password_hash"], password
        ):
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]

            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
