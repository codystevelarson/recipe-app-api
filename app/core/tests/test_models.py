from django.test import TestCase
from django.contrib.auth import get_user_model
from .. import models
from unittest.mock import patch


def sample_user(email='test@pizzacoffee.com', password='testpass'):
    ''' Create Sample User '''
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        ''' Test creating new user with email is successful '''
        email = 'test@pizzacoffee.net'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email, password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normailized(self):
        ''' Test the email for new user is normalized '''
        email = 'test@PIZZACOFFEE.NET'
        user = get_user_model().objects.create_user(
            email=email, password='test123'
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        ''' Test creating user with no email rasies errors '''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_new_super_user(self):
        ''' Test creating a new super user '''
        user = get_user_model().objects.create_superuser(
            email='test@test.com', password='test123')

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        ''' Test the tag string representation '''
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Gluten-Free'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredients_str(self):
        ''' Test the ingredient string representation '''
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Beef'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        ''' Test the recipe string representation '''
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='BBQ Ribs',
            time_minutes=300,
            price=25.99
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        ''' Test that image is saved in the correct location '''
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myImage.jpg')
        # Expected path
        exp_path = f'uploads/recipe/{uuid}.jpg'

        self.assertEqual(file_path, exp_path)
