from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from .models import Post, Comment, Like, Category
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CategorySerializer
)


class CategoryListView(APIView):
    """
    API endpoint for listing all post categories
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="List all categories",
        description="Get all available post categories. Creates default categories if they don't exist.",
        responses={
            200: CategorySerializer(many=True)
        },
        tags=['Categories']
    )
    def get(self, request):
        """Get list of all categories"""
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
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostListView(generics.ListAPIView):
    """
    API endpoint for listing published posts with optional category filtering
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer
    
    @extend_schema(
        summary="List all published posts",
        description="Get all published posts. Patients see posts marked as visible to patients, doctors see posts visible to staff. Can be filtered by category slug.",
        parameters=[
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter posts by category slug (e.g., "cardiology", "mental-health")',
                required=False
            )
        ],
        responses={
            200: PostListSerializer(many=True)
        },
        examples=[
            OpenApiExample(
                'Filter by Category',
                description='Example: /api/community/posts/?category=cardiology',
                value=[]
            )
        ],
        tags=['Posts']
    )
    def get(self, request, *args, **kwargs):
        """Get list of published posts"""
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.filter(status='published')

        if hasattr(user, 'patient_profile'):
            queryset = queryset.filter(visible_to_patients=True)
        elif hasattr(user, 'doctor_profile'):
            queryset = queryset.filter(visible_to_staff=True)

        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        
        return queryset
    
    def get_serializer_context(self):
        return {'request': self.request}


class PostCreateView(APIView):
    """
    API endpoint for doctors to create new posts
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        summary="Create a new post",
        description="Create a new community post. Only doctors can create posts. Supports multipart/form-data for image uploads.",
        request=PostCreateSerializer,
        responses={
            201: PostCreateSerializer,
            400: inline_serializer(
                name='PostCreateError',
                fields={'error': serializers.DictField()}
            ),
            403: inline_serializer(
                name='PostCreateForbidden',
                fields={'error': serializers.CharField()}
            )
        },
        examples=[
            OpenApiExample(
                'Create Post',
                value={
                    'title': 'Understanding Heart Health',
                    'category': 1,
                    'content': 'Detailed content about heart health...',
                    'excerpt': 'A brief guide to maintaining a healthy heart',
                    'status': 'published'
                },
                request_only=True
            )
        ],
        tags=['Posts']
    )
    def post(self, request):
        """Create a new post (doctors only)"""
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {"error": "Only doctors can create posts"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    """
    API endpoint for retrieving and deleting individual posts
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get post details",
        description="Retrieve detailed information about a specific post by its slug. Increments view count.",
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Unique slug identifier for the post'
            )
        ],
        responses={
            200: PostDetailSerializer,
            404: inline_serializer(
                name='PostNotFound',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Posts']
    )
    def get(self, request, slug):
        """Get post details by slug"""
        try:
            post = Post.objects.get(slug=slug, status='published')
            post.views_count += 1
            post.save(update_fields=['views_count'])
            
            serializer = PostDetailSerializer(post, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Delete a post",
        description="Delete a post. Only the author can delete their own posts.",
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Unique slug identifier for the post'
            )
        ],
        responses={
            204: inline_serializer(
                name='PostDeleteSuccess',
                fields={'message': serializers.CharField()}
            ),
            403: inline_serializer(
                name='PostDeleteForbidden',
                fields={'error': serializers.CharField()}
            ),
            404: inline_serializer(
                name='PostDeleteNotFound',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Posts']
    )
    def delete(self, request, slug):
        """Delete a post (author only)"""
        try:
            post = Post.objects.get(slug=slug)
            if post.author != request.user:
                return Response(
                    {"error": "You can only delete your own posts"},
                    status=status.HTTP_403_FORBIDDEN
                )
            post.delete()
            return Response(
                {"message": "Post deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class PostLikeView(APIView):
    """
    API endpoint for liking/unliking posts
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Like or unlike a post",
        description="Toggle like status on a post. If already liked, it will unlike. If not liked, it will add a like.",
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Unique slug identifier for the post'
            )
        ],
        responses={
            200: inline_serializer(
                name='PostLikeResponse',
                fields={
                    'message': serializers.CharField(),
                    'total_likes': serializers.IntegerField(),
                    'is_liked': serializers.BooleanField()
                }
            ),
            404: inline_serializer(
                name='PostLikeNotFound',
                fields={'error': serializers.CharField()}
            )
        },
        examples=[
            OpenApiExample(
                'Post Liked',
                value={
                    'message': 'Post liked',
                    'total_likes': 42,
                    'is_liked': True
                },
                response_only=True
            ),
            OpenApiExample(
                'Post Unliked',
                value={
                    'message': 'Post unliked',
                    'total_likes': 41,
                    'is_liked': False
                },
                response_only=True
            )
        ],
        tags=['Posts']
    )
    def post(self, request, slug):
        """Toggle like on a post"""
        try:
            post = Post.objects.get(slug=slug, status='published')
            
            like, created = Like.objects.get_or_create(post=post, user=request.user)
            
            if not created:
                like.delete()
                return Response(
                    {
                        "message": "Post unliked",
                        "total_likes": post.likes.count(),
                        "is_liked": False
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "message": "Post liked",
                        "total_likes": post.likes.count(),
                        "is_liked": True
                    },
                    status=status.HTTP_200_OK
                )
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class CommentListView(generics.ListAPIView):
    """
    API endpoint for listing comments on a post
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    
    @extend_schema(
        summary="List post comments",
        description="Get all approved top-level comments for a specific post. Includes nested replies.",
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Unique slug identifier for the post'
            )
        ],
        responses={
            200: CommentSerializer(many=True)
        },
        tags=['Comments']
    )
    def get(self, request, *args, **kwargs):
        """Get comments for a post"""
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        try:
            post = Post.objects.get(slug=slug, status='published')
            return post.comments.filter(is_approved=True, parent=None)
        except Post.DoesNotExist:
            return Comment.objects.none()


class CommentCreateView(APIView):
    """
    API endpoint for creating comments on posts
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Create a comment",
        description="Add a comment to a post. Can be a top-level comment or a reply to another comment by specifying parent ID.",
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Unique slug identifier for the post'
            )
        ],
        request=CommentCreateSerializer,
        responses={
            201: CommentCreateSerializer,
            400: inline_serializer(
                name='CommentCreateError',
                fields={'error': serializers.DictField()}
            ),
            404: inline_serializer(
                name='CommentPostNotFound',
                fields={'error': serializers.CharField()}
            )
        },
        examples=[
            OpenApiExample(
                'Top-level Comment',
                value={
                    'content': 'Great article! Very informative.',
                    'parent': None
                },
                request_only=True
            ),
            OpenApiExample(
                'Reply to Comment',
                value={
                    'content': 'I agree with your point!',
                    'parent': 5
                },
                request_only=True
            )
        ],
        tags=['Comments']
    )
    def post(self, request, slug):
        """Create a comment on a post"""
        try:
            post = Post.objects.get(slug=slug, status='published')
            serializer = CommentCreateSerializer(data=request.data)
            
            if serializer.is_valid():
                serializer.save(author=request.user, post=post)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class MyPostsView(generics.ListAPIView):
    """
    API endpoint for listing current user's posts
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer
    
    @extend_schema(
        summary="List my posts",
        description="Get all posts created by the current authenticated user (all statuses: draft, published, archived).",
        responses={
            200: PostListSerializer(many=True)
        },
        tags=['Posts']
    )
    def get(self, request, *args, **kwargs):
        """Get current user's posts"""
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}