import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_for_development")


# Conexao ao banco de dados
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Acessa colunas como dicionarios
    return conn


# Criar a tabela no banco de dados caso ela nao exista
def create_table():
    conn = get_db_connection()

    conn.execute(
        """
                 CREATE TABLE IF NOT EXISTS interessados (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nome TEXT NOT NULL,
                 email TEXT NOT NULL,
                 motivo TEXT
                 );
        """
    )

    conn.execute(
        """
                 CREATE TABLE IF NOT EXISTS admins (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL UNIQUE,
                 password TEXT NOT NULL
                 );
        """
    )
    conn.commit()
    conn.close()


# Chama a funcao para criar a tabela se necessario
create_table()


# Exibicao da Landing Page
@app.route("/")
def landing_page():
    return render_template("index.html")


# Processar dados do formulario
@app.route("/submit", methods=["POST"])
def submit_form():
    nome = request.form.get("nome")
    email = request.form.get("email")
    motivo = request.form.get("motivo")

    # Salvar os dados no banco
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO interessados (nome, email, motivo) VALUES (?, ?, ?)",
        (nome, email, motivo),
    )
    conn.commit()
    conn.close()

    # Informar sobre retorno em breve
    return render_template("obrigado.html", nome=nome)


# Listar interessados
@app.route("/interessados")
def listar_interessados():
    if not session.get("admin_logged_in"):
        # Se nao houver admin cadastrado, redireciona para setup, senao login
        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admins LIMIT 1").fetchone()
        conn.close()
        if not admin:
            return redirect(url_for("setup_admin"))
        return redirect(url_for("login"))

    conn = get_db_connection()
    interessados = conn.execute("SELECT * FROM interessados").fetchall()
    conn.close()
    return render_template("interessados.html", usuarios=interessados)


@app.route("/setup", methods=["GET", "POST"])
def setup_admin():
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins LIMIT 1").fetchone()

    if admin:
        conn.close()
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            hashed_password = generate_password_hash(password)
            conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            session["admin_logged_in"] = True
            return redirect(url_for("listar_interessados"))

    conn.close()
    return render_template("setup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin_logged_in"] = True
            return redirect(url_for("listar_interessados"))
        else:
            return render_template("login.html", error="Credenciais incorretas.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("landing_page"))


if __name__ == "__main__":
    app.run(debug=True)
