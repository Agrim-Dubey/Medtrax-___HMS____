from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser
from community.models import Category, Post, Comment

class PostCommentsAPITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="commenter_u", email="commu@med.com", password="P1")
        self.cat = Category.objects.create(name="Dentistry")
        self.post = Post.objects.create(
            title="Dental Health 101", author=self.user, category=self.cat,
            content="Brush twice daily...", status="published"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_and_list_comments(self):
        create_url = reverse("community:comment-create", kwargs={"slug": self.post.slug})
        payload = {"content": "Very informative tips on brushing!"}
        create_res = self.client.post(create_url, payload, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(post=self.post, content=payload["content"]).exists())

        list_url = reverse("community:comment-list", kwargs={"slug": self.post.slug})
        list_res = self.client.get(list_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(list_res.data) >= 1)
