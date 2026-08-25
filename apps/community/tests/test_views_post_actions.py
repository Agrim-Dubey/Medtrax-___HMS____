from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser
from community.models import Category, Post, Like

class PostActionsAPITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="poster_u", email="pu@med.com", password="P1")
        self.cat = Category.objects.create(name="General Health")
        self.post = Post.objects.create(
            title="Immunity Boosters", author=self.user, category=self.cat,
            content="Vitamin C and zinc...", status="published"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_new_community_post(self):
        url = reverse("community:post-create")
        payload = {
            "title": "Sleep Hygiene Advice",
            "category": self.cat.id,
            "content": "Tips for better sleep and circadian rhythms.",
            "status": "published"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title="Sleep Hygiene Advice").exists())

    def test_post_detail_increments_views(self):
        url = reverse("community:post-detail", kwargs={"slug": self.post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views_count, 1)

    def test_toggle_post_like(self):
        url = reverse("community:post-like", kwargs={"slug": self.post.slug})
        res1 = self.client.post(url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(Like.objects.filter(post=self.post, user=self.user).exists())

        res2 = self.client.post(url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(Like.objects.filter(post=self.post, user=self.user).exists())
