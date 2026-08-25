from django.test import TestCase
from authentication.models import CustomUser
from community.models import Category, Post

class CommunityCategoryAndPostModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="author1", email="a1@med.com", password="P1")
        self.cat = Category.objects.create(name="Cardiology Care", description="Heart health")

    def test_category_slug_generation(self):
        self.assertEqual(self.cat.slug, "cardiology-care")
        self.assertEqual(str(self.cat), "Cardiology Care")

    def test_post_creation_and_auto_slug(self):
        post = Post.objects.create(
            title="Understanding Heart Arrhythmia",
            author=self.user,
            category=self.cat,
            content="Detailed guide to heart rhythms...",
            status="published"
        )
        self.assertEqual(post.slug, "understanding-heart-arrhythmia")
        self.assertIsNotNone(post.published_at)
        self.assertEqual(str(post), "Understanding Heart Arrhythmia")
