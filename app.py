import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)


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
                 CREATE TABLE IF NOT EXISTS usuarios (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nome TEXT NOT NULL,
                 email TEXT NOT NULL,
                 motivo TEXT
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
        "INSERT INTO usuarios (nome, email, motivo) VALUES (?, ?, ?)",
        (nome, email, motivo),
    )
    conn.commit()
    conn.close()

    # Informar sobre retorno em breve
    return f"<h1>Obrigado, {nome}! Entraremos em contato em breve!</h1>"


# Listar interessados
@app.route("/interessados")
def listar_interessados():
    conn = get_db_connection()
    usuarios = conn.execute("SELECT * FROM usuarios").fetchall()
    conn.close()
    return render_template("interessados.html", usuarios=usuarios)


if __name__ == "__main__":
    app.run(debug=True)
