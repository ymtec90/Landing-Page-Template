import unittest
from app import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bem-vindo ao meu site!', response.data)

if __name__ == '__main__':
    unittest.main()
