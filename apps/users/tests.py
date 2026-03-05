from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

REGISTER_PAYLOAD = {
    'username': 'newuser',
    'email': 'newuser@example.com',
    'password': 'StrongPass123',
}


class AuthAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    # 1. Registration with valid data succeeds
    def test_registration_with_valid_data_succeeds(self):
        response = self.client.post('/api/auth/register/', REGISTER_PAYLOAD, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertNotIn('password', response.data)  # password must be write-only
        self.assertTrue(User.objects.filter(username='newuser').exists())

    # 2. Login returns JWT token pair
    def test_login_returns_jwt_token_pair(self):
        User.objects.create_user(username='loginuser', password='pass', email='login@example.com')
        response = self.client.post('/api/token/', {'username': 'loginuser', 'password': 'pass'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    # 3. Accessing protected endpoint without token returns 401
    def test_protected_endpoint_without_token_returns_401(self):
        # /bookings/ requires IsAuthenticated
        response = self.client.get('/bookings/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
