import sqlite3
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, session, redirect, url_for, abort

app = Flask(__name__)
secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    raise ValueError(
        "No FLASK_SECRET_KEY set for Flask app. Did you forget to set it?"
    )
app.secret_key = secret_key

# Configuracoes de validacao
MAX_NOME_LEN = 100
MAX_EMAIL_LEN = 255
MAX_MOTIVO_LEN = 1500
MAX_USERNAME_LEN = 50
MAX_PASSWORD_LEN = 128
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


# Conexao ao banco de dados
def get_db_connection():
    db_path = os.environ.get("DB_PATH", "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Acessa colunas como dicionarios
    return conn


# Criar a tabela no banco de dados caso ela nao exista
def create_table():
    conn = get_db_connection()

    # Check if old table exists
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='usuarios';"
    ).fetchone()

    if table_exists:
        conn.execute("ALTER TABLE usuarios RENAME TO interessados;")
    else:
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


# Exibicao da Landing Page
@app.route("/")
def landing_page():
    return render_template("index.html")


# Processar dados do formulario
@app.route("/submit", methods=["POST"])
def submit_form():
    nome = (request.form.get("nome") or "").strip()
    email = (request.form.get("email") or "").strip()
    motivo = (request.form.get("motivo") or "").strip()

    # Validacao basica
    if not nome or len(nome) > MAX_NOME_LEN:
        abort(400, description="Nome invalido ou muito longo.")
    if not email or len(email) > MAX_EMAIL_LEN or not EMAIL_REGEX.match(email):
        abort(400, description="E-mail invalido ou muito longo.")
    if not motivo or len(motivo) > MAX_MOTIVO_LEN:
        abort(400, description="Motivo invalido ou muito longo.")

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
            conn.execute(
                "INSERT INTO admins (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            conn.close()
            session["admin_logged_in"] = True
            return redirect(url_for("listar_interessados"))

    conn.close()
    return render_template("setup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or len(username) > MAX_USERNAME_LEN:
            abort(400, description="Usuario invalido ou muito longo.")
        if not password or len(password) > MAX_PASSWORD_LEN:
            abort(400, description="Senha invalida ou muito longa.")

        conn = get_db_connection()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin_logged_in"] = True
            return redirect(url_for("listar_interessados"))
        else:
            return render_template(
                "login.html", error="Credenciais incorretas."
            )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("landing_page"))


if __name__ == "__main__":
    # Chama a funcao para criar a tabela se necessario
    create_table()
    app.run(debug=True)
