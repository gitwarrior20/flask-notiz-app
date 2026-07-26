from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "mein-geheimer-schluessel"


def datenbank_starten():
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS notizen (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    user_id INTEGER
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    verbindung.commit()
    verbindung.close()


def notiz_speichern(text):
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["user"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        "INSERT INTO notizen (text, user_id) VALUES (?, ?)",
        (text, user[0])
    )

    verbindung.commit()
    verbindung.close()

def get_user_id():
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (session["user"],)
    )

    user = cursor.fetchone()

    verbindung.close()

    return user[0]

def notizen_laden():
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute(
    """
    SELECT id, text FROM notizen
    WHERE user_id = ?
    """,
    (get_user_id(),)
)

    daten = cursor.fetchall()

    verbindung.close()

    return daten


def notiz_loeschen(id):
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute(
        "DELETE FROM notizen WHERE id=?",
        (id,)
    )

    verbindung.commit()
    verbindung.close()

def notiz_bearbeiten(id, neuer_text):

    verbindung = sqlite3.connect("notizen.db")

    cursor = verbindung.cursor()

    cursor.execute(
        "UPDATE notizen SET text=? WHERE id=?",
        (neuer_text, id)
    )

    verbindung.commit()
    verbindung.close()


@app.route("/", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        neue_notiz = request.form["notiz"]

        if neue_notiz:
            notiz_speichern(neue_notiz)

    alle_notizen = notizen_laden()

    return render_template(
        "index.html",
        notizen=alle_notizen
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"],
            method="pbkdf2:sha256"
        )

        verbindung = sqlite3.connect("notizen.db")
        cursor = verbindung.cursor()

        cursor.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, password)
        )

        verbindung.commit()
        verbindung.close()

        return "Registrierung erfolgreich!"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        verbindung = sqlite3.connect("notizen.db")
        cursor = verbindung.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()

        verbindung.close()

        if user and check_password_hash(user[3], password):
            session["user"] = username
            return redirect("/")

        else:
            return "Falsche Daten!"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return "Logout funktioniert!"


@app.route("/loeschen/<int:id>")
def loeschen(id):

    notiz_loeschen(id)

    return redirect("/")

@app.route("/bearbeiten/<int:id>", methods=["POST"])
def bearbeiten(id):

    neuer_text = request.form["text"]

    notiz_bearbeiten(id, neuer_text)

    return redirect("/")
 
datenbank_starten()

if __name__ == "__main__":
    app.run(debug=True)