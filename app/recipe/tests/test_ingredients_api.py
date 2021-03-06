from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from ..serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def sample_user():
    return get_user_model().objects.create_user(
        'test@pizzacoffee.net', 'testpass'
    )


class PublicIngredientsApiTests(TestCase):
    ''' Test the publicly available ingredients API '''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        ''' Test that the login is required to access the endpoint '''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    ''' Test the private ingredients API '''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        ''' Test retrieving a list of ingredients '''
        Ingredient.objects.create(user=self.user, name='Bacon')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        ''' Test that ingredients for the authenticated user are returned '''
        user2 = get_user_model().objects.create_user(
            'test2@pizzacoffee.net', 'testpass'
        )
        Ingredient.objects.create(user=user2, name='Olive Oil')
        ingredient = Ingredient.objects.create(user=self.user, name='Banana')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredients_successful(self):
        ''' Test create a new ingredient '''
        payload = {'name': 'Onion'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user, name=payload['name']).exists()

        self.assertTrue(exists)

    def test_create_ingredients_invalid(self):
        ''' Test creating invalid ingredient fails '''
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredient_assigned_to_recipes(self):
        ''' Test filtering ingredients only assigned to recipes '''
        ing1 = Ingredient.objects.create(
            user=self.user, name='Apple'
        )

        ing2 = Ingredient.objects.create(
            user=self.user, name='Egg'
        )

        recipe = Recipe.objects.create(
            user=self.user,
            title='Apple Raw',
            time_minutes=1,
            price=0.89
        )
        recipe.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {'assigned-only': 1})

        ser1 = IngredientSerializer(ing1)
        ser2 = IngredientSerializer(ing2)

        self.assertIn(ser1.data, res.data)
        self.assertNotIn(ser2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        ''' Test filtering ingredients by assigned returns unique items '''
        ing = Ingredient.objects.create(
            user=self.user, name='Cheese'
        )
        Ingredient.objects.create(
            user=self.user, name='Apple'
        )

        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Cheese Plate',
            time_minutes=10,
            price=40.89
        )
        recipe1.ingredients.add(ing)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Cheese Sandwhich',
            time_minutes=10,
            price=3.89
        )
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned-only': 1})

        self.assertEqual(len(res.data), 1)
