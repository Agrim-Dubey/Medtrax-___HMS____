from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from community.models import Category

class CategoryListAPITests(APITestCase):
    def test_category_list_initializes_defaults(self):
        url = reverse("community:category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Category.objects.count() >= 1)
        self.assertTrue(len(response.data) >= 1)
