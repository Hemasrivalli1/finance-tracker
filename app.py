from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import matplotlib.pyplot as plt
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "secretkey"

# Database create
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        amount REAL,
        category TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",(username,password))
            conn.commit()
        except:
            return "User already exists"
        conn.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?",(username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (username,amount,category) VALUES (?,?,?)",
                       (username,amount,category))
        conn.commit()
        conn.close()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT amount,category FROM expenses WHERE username=?",(username,))
    data = cursor.fetchall()
    conn.close()

    # Chart generate
    categories = {}
    for amount,cat in data:
        categories[cat] = categories.get(cat,0) + amount

    if categories:
        plt.figure()
        plt.pie(categories.values(), labels=categories.keys(), autopct="%1.1f%%")
        plt.title("Expense Distribution")
        plt.savefig("static/chart.png")
        plt.close()

    return render_template("dashboard.html", data=data)

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
    