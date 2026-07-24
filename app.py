from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


def datenbank_starten():
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notizen (
        id INTEGER PRIMARY KEY,
        text TEXT NOT NULL
    )
    """)

    verbindung.commit()
    verbindung.close()


def notiz_speichern(text):
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute(
        "INSERT INTO notizen (text) VALUES (?)",
        (text,)
    )

    verbindung.commit()
    verbindung.close()


def notizen_laden():
    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute(
        "SELECT id, text FROM notizen"
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

    if request.method == "POST":

        neue_notiz = request.form["notiz"]

        if neue_notiz:
            notiz_speichern(neue_notiz)


    alle_notizen = notizen_laden()


    return render_template(
        "index.html",
        notizen=alle_notizen
    )

@app.route("/loeschen/<int:id>")
def loeschen(id):

    notiz_loeschen(id)

    return redirect("/")

@app.route("/bearbeiten/<int:id>", methods=["POST"])
def bearbeiten(id):

    neuer_text = request.form["text"]

    notiz_bearbeiten(id, neuer_text)

    return redirect("/")
if __name__ == "__main__":

    datenbank_starten()

    app.run(debug=True)