from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash

app = Flask(__name__)

app.secret_key = "mein-geheimer-schluessel"

import datetime

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
            AND papierkorb = 0
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
            AND papierkorb = 0
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
            AND papierkorb = 0
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
        UPDATE notizen
        SET papierkorb = 1
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
    kategorie = request.args.get("kategorie", "")


    alle_notizen = notizen_laden(
        suchbegriff,
        kategorie
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


    import datetime


    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()



    # Anzahl normale Notizen

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM notizen
        WHERE user_id = ?
        AND papierkorb = 0
        """,
        (get_user_id(),)
    )

    anzahl_notizen = cursor.fetchone()[0]




    # Kategorien

    cursor.execute(
        """
        SELECT kategorie, COUNT(*)
        FROM notizen
        WHERE user_id = ?
        AND papierkorb = 0
        GROUP BY kategorie
        """,
        (get_user_id(),)
    )

    kategorien = cursor.fetchall()


    anzahl_kategorien = len(kategorien)




    # Angeheftet

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM notizen
        WHERE user_id = ?
        AND angeheftet = 1
        AND papierkorb = 0
        """,
        (get_user_id(),)
    )

    angeheftet = cursor.fetchone()[0]





    # Papierkorb Anzahl

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM notizen
        WHERE user_id = ?
        AND papierkorb = 1
        """,
        (get_user_id(),)
    )

    papierkorb_anzahl = cursor.fetchone()[0]






    # Benutzer

    cursor.execute(
        """
        SELECT username, email
        FROM users
        WHERE username = ?
        """,
        (session["user"],)
    )

    user = cursor.fetchone()





    # Letzte Notiz

    cursor.execute(
        """
        SELECT text, datum
        FROM notizen
        WHERE user_id = ?
        AND papierkorb = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (get_user_id(),)
    )


    letzte_notiz = cursor.fetchone()



    if letzte_notiz:

        letzte_notiz = letzte_notiz

    else:

        letzte_notiz = ("Keine Notizen", "")







    # Letzte 5 Notizen

    cursor.execute(
        """
        SELECT text, datum
        FROM notizen
        WHERE user_id = ?
        AND papierkorb = 0
        ORDER BY id DESC
        LIMIT 5
        """,
        (get_user_id(),)
    )


    letzte_notizen = cursor.fetchall()



    verbindung.close()





    # Begrüßung nach Uhrzeit

    stunde = datetime.datetime.now().hour


    if stunde < 12:

        begruessung = "Guten Morgen ☀️"


    elif stunde < 18:

        begruessung = "Guten Tag 👋"


    else:

        begruessung = "Guten Abend 🌙"






    return render_template(
        "dashboard.html",

        anzahl_notizen=anzahl_notizen,

        user=user,

        kategorien=kategorien,

        anzahl_kategorien=anzahl_kategorien,

        angeheftet=angeheftet,

        papierkorb_anzahl=papierkorb_anzahl,

        letzte_notiz=letzte_notiz,

        letzte_notizen=letzte_notizen,

        begruessung=begruessung
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

@app.route("/papierkorb")
def papierkorb():

    if "user" not in session:
        return redirect("/login")


    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    cursor.execute(
        """
        SELECT id, text, datum
        FROM notizen
        WHERE user_id = ?
        AND papierkorb = 1
        ORDER BY id DESC
        """,
        (get_user_id(),)
    )


    notizen = cursor.fetchall()

    verbindung.close()


    return render_template(
        "papierkorb.html",
        notizen=notizen
    )

@app.route("/wiederherstellen/<int:id>")
def wiederherstellen(id):

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    cursor.execute(
        """
        UPDATE notizen
        SET papierkorb = 0
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


    flash(
        "Notiz wiederhergestellt!",
        "success"
    )


    return redirect("/papierkorb")

@app.route("/endgueltig_loeschen/<int:id>")
def endgueltig_loeschen(id):

    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    cursor.execute(
        """
        DELETE FROM notizen
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


    flash(
        "Notiz endgültig gelöscht!",
        "success"
    )


    return redirect("/papierkorb")

@app.route("/papierkorb_leeren")
def papierkorb_leeren():

    if "user" not in session:
        return redirect("/login")


    verbindung = sqlite3.connect("notizen.db")
    cursor = verbindung.cursor()


    cursor.execute(
        """
        DELETE FROM notizen
        WHERE user_id = ?
        AND papierkorb = 1
        """,
        (get_user_id(),)
    )


    verbindung.commit()
    verbindung.close()


    flash(
        "Papierkorb wurde geleert!",
        "success"
    )


    return redirect("/papierkorb")

datenbank_starten()


if __name__ == "__main__":
    app.run(debug=True)