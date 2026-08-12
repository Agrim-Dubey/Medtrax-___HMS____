from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser
from community.models import Category, Post

class PostListAPITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="reader1", email="r1@med.com", password="P1")
        self.cat1 = Category.objects.create(name="Mental Health")
        self.cat2 = Category.objects.create(name="Nutrition")
        Post.objects.create(
            title="Mindfulness Basics", author=self.user, category=self.cat1,
            content="Meditation guide...", status="published"
        )
        Post.objects.create(
            title="Healthy Eating", author=self.user, category=self.cat2,
            content="Balanced diet tips...", status="published"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_all_published_posts(self):
        url = reverse("community:post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_posts_by_category_slug(self):
        url = reverse("community:post-list")
        response = self.client.get(f"{url}?category={self.cat1.slug}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Mindfulness Basics")
