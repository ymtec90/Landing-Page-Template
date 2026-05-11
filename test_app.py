import unittest
import tempfile
import os
import sqlite3
import app as flask_app
from unittest.mock import patch

class ListarInteressadosTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        flask_app.app.config['TESTING'] = True
        self.client = flask_app.app.test_client()

        def mock_get_db_connection():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

        self.patcher = patch('app.get_db_connection', side_effect=mock_get_db_connection)
        self.mock_get_db = self.patcher.start()

        # Create tables in the temp db
        flask_app.create_table()

    def tearDown(self):
        self.patcher.stop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_listar_interessados_no_admin_setup_redirect(self):
        # No admin in DB, not logged in
        response = self.client.get('/interessados')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/setup', response.headers['Location'])

    def test_listar_interessados_admin_exists_login_redirect(self):
        # Admin exists in DB, not logged in
        conn = self.mock_get_db()
        conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "hashed"))
        conn.commit()
        conn.close()

        response = self.client.get('/interessados')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_listar_interessados_logged_in(self):
        # Admin logged in
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        # Add some mock interessados
        conn = self.mock_get_db()
        conn.execute("INSERT INTO interessados (nome, email, motivo) VALUES (?, ?, ?)", ("João", "joao@example.com", "Interesse em TI"))
        conn.commit()
        conn.close()

        response = self.client.get('/interessados')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jo\xc3\xa3o', response.data)
        self.assertIn(b'joao@example.com', response.data)

if __name__ == '__main__':
    unittest.main()
