from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def sample_user():
    return get_user_model().objects.create_user(
        'test@pizzacoffee.net', 'testpass'
    )


class PublicTagsTests(TestCase):
    ''' Test the publicly available tags API '''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        ''' Test that login is required for retrieving tags '''
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    ''' Test the authorized user tags API '''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        ''' Test retrieving tags '''
        Tag.objects.create(user=self.user, name='Gluten-Free')
        Tag.objects.create(user=self.user, name='Vegan')

        res = self.client.get(TAGS_URL)

        # Pull tags directly from db and serailize them
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        ''' Test that tags are returned for the authenticated user '''
        user2 = get_user_model().objects.create_user(
            'other@pizzacoffee.net', 'testpass')

        # Create a user2 tag
        Tag.objects.create(user=user2, name='Breakfast')
        # Create a test setup user tag
        tag = Tag.objects.create(user=self.user, name='Dinner')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        ''' Test creating a new tag '''
        payload = {'name': 'Test Tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        ''' Creating a new tag with invalid payload '''
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
