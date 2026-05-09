from django.db import transaction
from Authapi.models import CustomUser
from .models import Post, Comment, Like, Category
from .serializers import PostCreateSerializer, CommentCreateSerializer

def initialize_default_categories():
    default_categories = [
        {'name': 'General Medicine', 'description': 'General health topics'},
        {'name': 'Cardiology', 'description': 'Heart health'},
        {'name': 'Pediatrics', 'description': 'Child health'},
        {'name': 'Mental Health', 'description': 'Mental wellness'},
        {'name': 'Nutrition', 'description': 'Diet advice'},
        {'name': 'Fitness', 'description': 'Exercise tips'},
    ]
    for cat_data in default_categories:
        Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )

@transaction.atomic
def create_community_post(*, author: CustomUser, data: dict) -> Post:
    serializer = PostCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save(author=author)

@transaction.atomic
def delete_community_post(*, post: Post):
    post.delete()

@transaction.atomic
def toggle_post_like(*, post: Post, user: CustomUser) -> dict:
    like, created = Like.objects.get_or_create(post=post, user=user)
    if not created:
        like.delete()
        return {"message": "Post unliked", "total_likes": post.likes.count(), "is_liked": False}
    return {"message": "Post liked", "total_likes": post.likes.count(), "is_liked": True}

@transaction.atomic
def create_post_comment(*, post: Post, author: CustomUser, data: dict) -> Comment:
    serializer = CommentCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save(author=author, post=post)

@transaction.atomic
def increment_post_view_count(*, post: Post):
    post.views_count += 1
    post.save(update_fields=['views_count'])
