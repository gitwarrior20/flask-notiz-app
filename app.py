from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash

app = Flask(__name__)

app.secret_key = "mein-geheimer-schluessel"


def datenbank_starten():

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notizen (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    user_id INTEGER,
    datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

import datetime

def notiz_speichern(text, kategorie):

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    datum = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")


    cursor.execute(
        """
        INSERT INTO notizen
        (text, user_id, datum, bearbeitet, kategorie)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            text,
            get_user_id(),
            datum,
            datum,
            kategorie
        )
    )


    verbindung.commit()
    verbindung.close()


def notizen_laden(suche="", kategorie=""):

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    if kategorie:

        cursor.execute(
            """
            SELECT id, text, datum, bearbeitet, angeheftet, kategorie
            FROM notizen
            WHERE user_id = ?
            AND kategorie = ?
            ORDER BY angeheftet DESC, id DESC
            """,
            (
                get_user_id(),
                kategorie
            )
        )


    elif suche:

        cursor.execute(
            """
            SELECT id, text, datum, bearbeitet, angeheftet, kategorie
            FROM notizen
            WHERE user_id = ?
            AND text LIKE ?
            ORDER BY angeheftet DESC, id DESC
            """,
            (
                get_user_id(),
                "%" + suche + "%"
            )
        )


    else:

        cursor.execute(
            """
            SELECT id, text, datum, bearbeitet, angeheftet, kategorie
            FROM notizen
            WHERE user_id = ?
            ORDER BY angeheftet DESC, id DESC
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
        """
        DELETE FROM notizen
        WHERE id = ?
        AND user_id = ?
        """,
        (id, get_user_id())
    )

    verbindung.commit()
    verbindung.close()


def notiz_bearbeiten(id, neuer_text, kategorie):

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()

    zeit = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    cursor.execute(
        """
        UPDATE notizen
        SET text=?, bearbeitet=?, kategorie=?
        WHERE id=? AND user_id=?
        """,
        (
            neuer_text,
            zeit,
            kategorie,
            id,
            get_user_id()
        )
    )

    verbindung.commit()
    verbindung.close()

def notiz_anheften(id):

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    cursor.execute(
        """
        UPDATE notizen
        SET angeheftet =
        CASE
            WHEN angeheftet = 0 THEN 1
            ELSE 0
        END
        WHERE id = ?
        AND user_id = ?
        """,
        (
            id,
            get_user_id()
        )
    )


    verbindung.commit()
    verbindung.close()

@app.route("/", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect("/login")


    if request.method == "POST":

        neue_notiz = request.form["notiz"]
        kategorie = request.form["kategorie"]

        if neue_notiz:
            notiz_speichern(neue_notiz, kategorie)


    suchbegriff = request.args.get("suche", "")
    kategorie_filter = request.args.get("kategorie", "")


    alle_notizen = notizen_laden(
        suchbegriff,
        kategorie_filter
    )


    return render_template(
        "index.html",
        notizen=alle_notizen
    )



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        klares_passwort = request.form["password"]

        if len(klares_passwort) < 8:

            flash(

                "Das Passwort muss mindestens 8 Zeichen haben!",

                "error"

            )

            return redirect("/register")

        password = generate_password_hash(

            klares_passwort,

            method="pbkdf2:sha256"

        )


        verbindung = sqlite3.connect("notizen.db")
        cursor = verbindung.cursor()


        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )


        if cursor.fetchone():

            verbindung.close()

            flash(
                "Benutzername existiert bereits!",
                "error"
            )

            return redirect("/register")



        cursor.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, password)
        )


        verbindung.commit()
        verbindung.close()


        flash("Registrierung erfolgreich! Du kannst dich jetzt einloggen.", "success")
        
        return redirect("/login")


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

            flash(
                "Erfolgreich eingeloggt!",
                "success"
            )

            return redirect("/")


        else:

            flash(
                "Falscher Benutzername oder Passwort!",
                "error"
            )

            return redirect("/login")


    return render_template("login.html")



@app.route("/logout")
def logout():

    session.pop("user", None)

    flash("Du wurdest erfolgreich abgemeldet.", "success")

    return redirect("/login")



@app.route("/loeschen/<int:id>")
def loeschen(id):

    notiz_loeschen(id)

    return redirect("/")



@app.route("/bearbeiten/<int:id>", methods=["POST"])
def bearbeiten(id):

    neuer_text = request.form["text"]

    kategorie = request.form["kategorie"]


    notiz_bearbeiten(
        id,
        neuer_text,
        kategorie
    )


    flash(
        "Notiz wurde aktualisiert!",
        "success"
    )


    return redirect("/")

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")


    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    # Anzahl Notizen
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM notizen
        WHERE user_id = ?
        """,
        (get_user_id(),)
    )

    anzahl_notizen = cursor.fetchone()[0]



    # Benutzerinformationen
    cursor.execute(
        """
        SELECT username, email
        FROM users
        WHERE username = ?
        """,
        (session["user"],)
    )

    user = cursor.fetchone()



    # letzte Bearbeitung
    cursor.execute(
        """
        SELECT bearbeitet
        FROM notizen
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (get_user_id(),)
    )

    letzte_aktivitaet = cursor.fetchone()


    if letzte_aktivitaet:
        letzte_aktivitaet = letzte_aktivitaet[0]
    else:
        letzte_aktivitaet = "Noch keine Notizen"



    verbindung.close()



    return render_template(
        "dashboard.html",
        anzahl_notizen=anzahl_notizen,
        user=user,
        letzte_aktivitaet=letzte_aktivitaet
    )



@app.route("/profil", methods=["GET", "POST"])
def profil():

    if "user" not in session:
        return redirect("/login")


    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    if request.method == "POST":

        aktion = request.form["aktion"]


        if aktion == "email":

            neue_email = request.form["email"]


            if "@" not in neue_email:

                flash(
                    "Bitte eine gültige E-Mail eingeben!",
                    "error"
                )

            else:

                cursor.execute(
                    """
                    UPDATE users
                    SET email = ?
                    WHERE username = ?
                    """,
                    (
                        neue_email,
                        session["user"]
                    )
                )

                verbindung.commit()


                flash(
                    "E-Mail erfolgreich geändert!",
                    "success"
                )



        elif aktion == "passwort":

            altes_passwort = request.form["alt"]
            neues_passwort = request.form["neu"]
            bestaetigung = request.form["bestaetigung"]


            cursor.execute(
                """
                SELECT password
                FROM users
                WHERE username = ?
                """,
                (session["user"],)
            )


            user_passwort = cursor.fetchone()



            if not check_password_hash(user_passwort[0], altes_passwort):

                flash(
                    "Altes Passwort ist falsch!",
                    "error"
                )


            elif len(neues_passwort) < 8:

                flash(
                    "Das neue Passwort muss mindestens 8 Zeichen haben!",
                    "error"
                )


            elif neues_passwort != bestaetigung:

                flash(
                    "Passwörter stimmen nicht überein!",
                    "error"
                )


            else:

                neues_hash = generate_password_hash(
                    neues_passwort,
                    method="pbkdf2:sha256"
                )


                cursor.execute(
                    """
                    UPDATE users
                    SET password = ?
                    WHERE username = ?
                    """,
                    (
                        neues_hash,
                        session["user"]
                    )
                )


                verbindung.commit()


                flash(
                    "Passwort erfolgreich geändert!",
                    "success"
                )



    cursor.execute(
        """
        SELECT username, email
        FROM users
        WHERE username = ?
        """,
        (session["user"],)
    )


    user = cursor.fetchone()


    verbindung.close()


    return render_template(
        "profil.html",
        user=user
    )

@app.route("/anheften/<int:id>")
def anheften(id):

    if "user" not in session:
        return redirect("/login")

    notiz_anheften(id)

    flash("Notiz wurde geändert!", "success")

    return redirect("/")

datenbank_starten()


if __name__ == "__main__":
    app.run(debug=True)