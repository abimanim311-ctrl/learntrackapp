import unittest
from unittest.mock import MagicMock, patch
import datetime
from app import app, update_streak

class LearnTrackTestCase(unittest.TestCase):
    def setUp(self):
        """Configure test client and mock database adapters."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret'
        self.client = app.test_client()

    def test_app_config(self):
        """Verify configurations are loaded correctly."""
        self.assertTrue(app.config['TESTING'])
        self.assertFalse(app.config['WTF_CSRF_ENABLED'])
        self.assertEqual(app.config['MAX_CONTENT_LENGTH'], 2 * 1024 * 1024)

    def test_public_routes(self):
        """Test public endpoints (login, register)."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign in to track your learning journey', response.data)

        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create your account to start tracking progress', response.data)

    def test_unauthorized_redirects(self):
        """Verify route security gates redirect to login for anonymous requests."""
        protected_routes = ['/dashboard', '/goals', '/goals/add', '/profile', '/admin']
        for route in protected_routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login', response.headers.get('Location', ''))

    @patch('app.mysql')
    def test_streak_calculation_new_user(self, mock_mysql):
        """Test streak initialization for a user with no previous logs."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_mysql.connection = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate no streak record
        mock_cursor.fetchone.return_value = None 
        
        user_id = 99
        study_date = datetime.date(2026, 6, 12)
        
        update_streak(user_id, study_date)
        
        # Verify cursor execution checks and inserts new streak
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM streaks WHERE user_id = %s", (user_id,)
        )
        mock_cursor.execute.assert_any_call(
            "INSERT INTO streaks (user_id, current_streak, longest_streak, last_checkin) VALUES (%s, 1, 1, %s)",
            (user_id, study_date)
        )

    @patch('app.mysql')
    def test_streak_calculation_consecutive(self, mock_mysql):
        """Test streak increments on consecutive study day."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_mysql.connection = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate active streak of 5 days, last checked in yesterday (June 11)
        mock_cursor.fetchone.return_value = {
            'user_id': 99,
            'current_streak': 5,
            'longest_streak': 5,
            'last_checkin': datetime.date(2026, 6, 11)
        }
        
        user_id = 99
        study_date = datetime.date(2026, 6, 12)
        
        update_streak(user_id, study_date)
        
        # Verify streak increments to 6 and updates DB
        mock_cursor.execute.assert_any_call(
            "UPDATE streaks SET current_streak = %s, longest_streak = %s, last_checkin = %s WHERE user_id = %s",
            (6, 6, study_date, user_id)
        )

    @patch('app.mysql')
    def test_streak_calculation_broken(self, mock_mysql):
        """Test streak resets to 1 if consecutive day is missed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_mysql.connection = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate active streak of 5 days, last checked in 5 days ago (June 7)
        mock_cursor.fetchone.return_value = {
            'user_id': 99,
            'current_streak': 5,
            'longest_streak': 8,
            'last_checkin': datetime.date(2026, 6, 7)
        }
        
        user_id = 99
        study_date = datetime.date(2026, 6, 12)
        
        update_streak(user_id, study_date)
        
        # Verify streak resets to 1 and updates DB
        mock_cursor.execute.assert_any_call(
            "UPDATE streaks SET current_streak = 1, last_checkin = %s WHERE user_id = %s",
            (study_date, user_id)
        )

if __name__ == '__main__':
    unittest.main()
