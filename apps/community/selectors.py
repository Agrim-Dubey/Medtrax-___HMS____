from django.db.models import QuerySet
from Authapi.models import CustomUser
from .models import Post, Comment, Category

def get_all_categories() -> QuerySet[Category]:
    return Category.objects.all()

def get_community_posts(*, user: CustomUser, category_slug: str = None) -> QuerySet[Post]:
    queryset = Post.objects.filter(status='published')

    if hasattr(user, 'patient_profile'):
        queryset = queryset.filter(visible_to_patients=True)
    elif hasattr(user, 'doctor_profile'):
        queryset = queryset.filter(visible_to_staff=True)

    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
        
    return queryset.order_by('-created_at')

def get_post_detail(*, slug: str) -> Post:
    try:
        return Post.objects.get(slug=slug, status='published')
    except Post.DoesNotExist:
        return None

def get_post_comments(*, post_slug: str) -> QuerySet[Comment]:
    try:
        post = Post.objects.get(slug=post_slug, status='published')
        return post.comments.filter(is_approved=True, parent=None)
    except Post.DoesNotExist:
        return Comment.objects.none()

def get_user_posts(*, user: CustomUser) -> QuerySet[Post]:
    return Post.objects.filter(author=user).order_by('-created_at')
