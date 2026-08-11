from django.test import TestCase
from Authapi.models import CustomUser
from community.models import Category, Post, Comment, Like

class EngagementModelsTests(TestCase):
    def setUp(self):
        self.u1 = CustomUser.objects.create_user(username="comm_u1", email="cu1@med.com", password="P1")
        self.u2 = CustomUser.objects.create_user(username="comm_u2", email="cu2@med.com", password="P1")
        self.cat = Category.objects.create(name="Wellness", description="Health tips")
        self.post = Post.objects.create(
            title="Daily Hydration", author=self.u1, category=self.cat,
            content="Drink 8 glasses of water...", status="published"
        )

    def test_nested_comments_creation(self):
        parent_c = Comment.objects.create(post=self.post, author=self.u2, content="Great article!")
        reply_c = Comment.objects.create(post=self.post, author=self.u1, content="Thank you!", parent=parent_c)
        self.assertIn("Great article!", str(parent_c))
        self.assertEqual(parent_c.replies.count(), 1)
        self.assertEqual(reply_c.parent, parent_c)

    def test_like_model_representation(self):
        like = Like.objects.create(post=self.post, user=self.u2)
        self.assertIn("comm_u2 likes Daily Hydration", str(like))
