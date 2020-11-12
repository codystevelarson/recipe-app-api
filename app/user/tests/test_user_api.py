from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUsersApiTests(TestCase):
    ''' Test the users API (Public) '''

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        ''' Test creating user with valid payload is successful '''
        payload = {
            'email': 'test@test.com',
            'password': 'test123',
            'name': 'Testy Jr.'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        ''' Test creating a user that already exists fails '''
        payload = {
            'email': 'test@test.com',
            'password': 'test123',
            'name': 'Testy Jr.'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        ''' Test that the password must be more than 5 characters '''
        payload = {
            'email': 'test@test.com',
            'password': 'pw',
            'name': 'Test Jr.'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        ''' Test that a token is created for the user '''
        # Create a new user
        payload = {'email': 'test@test.com', 'password': 'test123'}
        create_user(**payload)

        # Get token for new user
        res = self.client.post(TOKEN_URL, payload)

        # Check if token key is in response
        self.assertIn('token', res.data)

        # Check for OK response
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_creds(self):
        ''' Token is not created if invalid credentials are given '''
        # Create a new user
        new_user = {'email': 'test@test.com', 'password': 'test123'}
        create_user(**new_user)

        payload = {'email': 'test@test.com', 'password': 'wrongpassword'}
        res = self.client.post(TOKEN_URL, payload)

        # Check token is not returned and response is 400
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        ''' Test token is not created if user doesn't exist '''
        # Don't create a new user just pass in a user model
        payload = {'email': 'test@test.com', 'password': 'test123'}
        res = self.client.post(TOKEN_URL, payload)

        # Check token is not returned and response is 400
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        ''' Test that email and password are required '''
        res = self.client.post(
            TOKEN_URL, {'email': 'something', 'password': ''})

        # Check token is not returned and response is 400
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
