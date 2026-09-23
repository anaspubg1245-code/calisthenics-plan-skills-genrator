from flask import Flask, render_template, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

# Change this to a long random secret before
# using the application outside your computer.
app.secret_key = "vishalthenics-development-secret-key"

DATABASE = "vishalthenics.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():

    db = sqlite3.connect(DATABASE)

    # Allows us to access columns by name
    db.row_factory = sqlite3.Row

    return db


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            level TEXT DEFAULT 'Beginner',

            goal TEXT DEFAULT 'Strength',

            training_days INTEGER DEFAULT 3

        )
    """)

    db.commit()

    db.close()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def index():

    return render_template("index.html")


# ==========================================
# SIGN UP
# ==========================================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400


    username = data.get("username", "").strip()

    email = data.get("email", "").strip()

    password = data.get("password", "")

    confirm_password = data.get(
        "confirm_password",
        ""
    )


    # -----------------------------
    # VALIDATION
    # -----------------------------

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400


    if password != confirm_password:

        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400


    if len(password) < 8:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 8 characters."
        }), 400


    # -----------------------------
    # DATABASE
    # -----------------------------

    db = get_db()


    existing_user = db.execute(
        """
        SELECT id
        FROM users
        WHERE username = ? OR email = ?
        """,
        (username, email)
    ).fetchone()


    if existing_user:

        db.close()

        return jsonify({
            "success": False,
            "message": "Username or email already exists."
        }), 409


    # -----------------------------
    # HASH PASSWORD
    # -----------------------------

    hashed_password = generate_password_hash(
        password
    )


    # -----------------------------
    # INSERT USER
    # -----------------------------

    db.execute(
        """
        INSERT INTO users
        (
            username,
            email,
            password
        )

        VALUES (?, ?, ?)
        """,
        (
            username,
            email,
            hashed_password
        )
    )


    db.commit()

    db.close()


    return jsonify({
        "success": True,
        "message": "Account created successfully."
    })


# ==========================================
# LOGIN
# ==========================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()


    if not data:

        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400


    username = data.get(
        "username",
        ""
    ).strip()


    password = data.get(
        "password",
        ""
    )


    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Enter username and password."
        }), 400


    db = get_db()


    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    db.close()


    # -----------------------------
    # CHECK USER
    # -----------------------------

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401


    # -----------------------------
    # CHECK PASSWORD
    # -----------------------------

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401


    # -----------------------------
    # CREATE SESSION
    # -----------------------------

    session["user_id"] = user["id"]

    session["username"] = user["username"]


    return jsonify({

        "success": True,

        "message": "Login successful.",

        "username": user["username"],

        "level": user["level"],

        "goal": user["goal"],

        "training_days": user["training_days"]

    })


# ==========================================
# CURRENT USER
# ==========================================

@app.route("/api/me")
def current_user():

    if "user_id" not in session:

        return jsonify({
            "logged_in": False
        })


    db = get_db()


    user = db.execute(
        """
        SELECT
            id,
            username,
            email,
            level,
            goal,
            training_days
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    db.close()


    if not user:

        session.clear()

        return jsonify({
            "logged_in": False
        })


    return jsonify({

        "logged_in": True,

        "user": {

            "id": user["id"],

            "username": user["username"],

            "email": user["email"],

            "level": user["level"],

            "goal": user["goal"],

            "training_days": user["training_days"]

        }

    })


# ==========================================
# UPDATE TRAINING PREFERENCES
# ==========================================

@app.route("/api/preferences", methods=["POST"])
def update_preferences():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    data = request.get_json()


    level = data.get(
        "level",
        "Beginner"
    )


    goal = data.get(
        "goal",
        "Strength"
    )


    training_days = data.get(
        "training_days",
        3
    )


    # -----------------------------
    # ALLOWED VALUES
    # -----------------------------

    allowed_levels = [

        "Beginner",
        "Intermediate",
        "Advanced"

    ]


    allowed_goals = [

        "Strength",
        "Skill",
        "Handstand",
        "Core",
        "Pullup"

    ]


    if level not in allowed_levels:

        return jsonify({
            "success": False,
            "message": "Invalid training level."
        }), 400


    if goal not in allowed_goals:

        return jsonify({
            "success": False,
            "message": "Invalid training goal."
        }), 400


    try:

        training_days = int(
            training_days
        )

    except:

        return jsonify({
            "success": False,
            "message": "Training days must be a number."
        }), 400


    if training_days < 1 or training_days > 7:

        return jsonify({
            "success": False,
            "message": "Training days must be between 1 and 7."
        }), 400


    # -----------------------------
    # SAVE
    # -----------------------------

    db = get_db()


    db.execute(
        """
        UPDATE users

        SET
            level = ?,
            goal = ?,
            training_days = ?

        WHERE id = ?
        """,
        (
            level,
            goal,
            training_days,
            session["user_id"]
        )
    )


    db.commit()

    db.close()


    return jsonify({

        "success": True,

        "message": "Preferences saved."

    })


# ==========================================
# GENERATE PLAN
# ==========================================

@app.route("/api/generate-plan", methods=["POST"])
def generate_plan():

    if "user_id" not in session:

        return jsonify({

            "success": False,

            "message": "Please login first."

        }), 401


    data = request.get_json()


    level = data.get(
        "level",
        "Beginner"
    )


    goal = data.get(
        "goal",
        "Strength"
    )


    training_days = data.get(
        "training_days",
        3
    )


    # -----------------------------
    # PLAN DATABASE
    # -----------------------------

    plans = {

        "Strength": [

            "Controlled push-up practice",

            "Bodyweight squat practice",

            "Assisted pulling practice",

            "Gentle core exercises"

        ],


        "Skill": [

            "Basic balance practice",

            "Technique practice",

            "Controlled pushing movements",

            "Controlled pulling movements"

        ],


        "Handstand": [

            "Wrist preparation",

            "Wall-supported balance practice",

            "Shoulder control exercises",

            "Short technique sessions"

        ],


        "Core": [

            "Dead-bug variations",

            "Plank variations",

            "Hollow-body preparation",

            "Controlled leg exercises"

        ],


        "Pullup": [

            "Scapular control",

            "Assisted pull-ups",

            "Controlled pulling practice",

            "Grip practice"

        ]

    }


    exercises = plans.get(

        goal,

        plans["Strength"]

    )


    # -----------------------------
    # CREATE RESPONSE
    # -----------------------------

    plan = {

        "level": level,

        "goal": goal,

        "training_days": training_days,

        "exercises": exercises

    }


    return jsonify({

        "success": True,

        "plan": plan

    })


# ==========================================
# LOGOUT
# ==========================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()


    return jsonify({

        "success": True,

        "message": "Logged out successfully."

    })


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True
    )