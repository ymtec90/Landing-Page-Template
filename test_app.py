import unittest
import sqlite3
from app import get_db_connection

class TestApp(unittest.TestCase):
    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        self.assertEqual(conn.row_factory, sqlite3.Row)
        conn.close()

if __name__ == '__main__':
    unittest.main()
