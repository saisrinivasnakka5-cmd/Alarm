from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")
DB_PATH = os.getenv("DATABASE_NAME", "mess_alarm.db")

DEFAULT_MEALS = [
    ("Breakfast", "07:30"),
    ("Lunch", "12:30"),
    ("Dinner", "19:30"),
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                meal_time TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM meals").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO meals (name, meal_time, enabled) VALUES (?, ?, 1)",
                DEFAULT_MEALS
            )

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        meal_id = request.form.get("meal_id", type=int)
        meal_time = request.form.get("meal_time", "")
        enabled = 1 if request.form.get("enabled") == "on" else 0
        try:
            datetime.strptime(meal_time, "%H:%M")
            with connect_db() as conn:
                conn.execute(
                    "UPDATE meals SET meal_time = ?, enabled = ? WHERE id = ?",
                    (meal_time, enabled, meal_id)
                )
            flash("Meal reminder saved.", "success")
        except ValueError:
            flash("Please choose a valid time.", "error")
        return redirect(url_for("index"))

    with connect_db() as conn:
        meals = conn.execute("SELECT * FROM meals ORDER BY id").fetchall()
    return render_template("index.html", meals=meals)

@app.route("/api/meals")
def api_meals():
    with connect_db() as conn:
        meals = conn.execute(
            "SELECT id, name, meal_time, enabled FROM meals ORDER BY id"
        ).fetchall()
    return {"meals": [dict(m) for m in meals]}

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
