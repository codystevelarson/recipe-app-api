from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from ..serializers import RecipeSerializer, RecipeDetailSerializer

# /api/recipe/recipes
RECIPE_URL = reverse('recipe:recipe-list')


# /api/recipe/recipes/{id}
def detail_url(recipe_id):
    ''' Return recipe detail url '''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_user():
    ''' Create a smaple test user '''
    return get_user_model().objects.create_user(
        'test@pizzacoffee.net', 'testpass'
    )


def sample_tag(user, name='Main course'):
    ''' Create and return a sample tag '''
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sauce'):
    ''' Create and return a sample ingredient '''
    return Ingredient.objects.create(user=user, name=name)


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

    def test_retrieve_recipes(self):
        ''' Test retrieving a list of recipes '''
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        ''' Test retrieving recipes for user '''
        user2 = get_user_model().objects.create_user(
            'test2@pizzacoffee.net', 'testpass'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        ''' Test viewing a recipe detail '''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        ''' Test creating recipe '''
        payload = {
            'title': 'Cheese Bread',
            'time_minutes': 10,
            'price': 3.50
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        ''' Test creating a recipe with tags '''
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Breakfast')

        payload = {
            'title': 'Vegan Pancake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 25,
            'price': 15.75
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        ''' Test creating a recipe with ingredients '''
        ing1 = sample_ingredient(user=self.user, name='Olive Oil')
        ing2 = sample_ingredient(user=self.user, name='Peanut')

        payload = {
            'title': 'Sauteed peanut',
            'ingredients': [ing1.id, ing2.id],
            'time_minutes': 5,
            'price': 11.25
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ings = recipe.ingredients.all()

        self.assertEqual(ings.count(), 2)
        self.assertIn(ing1, ings)
        self.assertIn(ing2, ings)
