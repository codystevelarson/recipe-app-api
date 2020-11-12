from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from ..serializers import RecipeSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def sample_user():
    ''' Create a smaple test user '''
    return get_user_model().objects.create_user(
        'test@pizzacoffee.net', 'testpass'
    )


def sample_recipe(user, **params):
    ''' Create and return a smaple recipe '''
    defaults = {'title': 'sample recipe', 'time_minutes': 10, 'price': 5.99}
    # Update overrides or creates new key/values
    # if key is not found in dictionary
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTest(TestCase):
    ''' Test unauthenticated recipe API access '''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        ''' Test that authentication is required '''
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    ''' Test authenticated recipe access '''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipies(self):
        ''' Test retrieving a list of recipies '''
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipies = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipies_limited_to_user(self):
        ''' Test retrieving recipies for user '''
        user2 = get_user_model().objects.create_user(
            'test2@pizzacoffee.net', 'testpass'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipies = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
