from rest_framework import status, generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q

from .models import Post, Comment, Like, Category
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CategorySerializer
)
from .selectors import (
    get_all_categories,
    get_community_posts,
    get_post_detail,
    get_post_comments,
    get_user_posts
)
from .services import (
    initialize_default_categories,
    create_community_post,
    delete_community_post,
    toggle_post_like,
    create_post_comment,
    increment_post_view_count
)

class CategoryListView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_summary="List all categories",
        operation_description="Fetch all post categories available in the community board. Default categories are auto-created if missing.",
        responses={
            200: openapi.Response(
                description="List of available categories",
                examples={
                    "application/json": [
                        {"id": 1, "name": "Cardiology", "description": "Heart-related topics"},
                        {"id": 2, "name": "Mental Health", "description": "Discussion on mental wellness"}
                    ]
                }
            )
        },
        tags=['Categories']
    )
    def get(self, request):
        initialize_default_categories()
        categories = get_all_categories()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class PostListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer

    @swagger_auto_schema(
        operation_summary="List all published posts",
        operation_description=(
            "Retrieve all published posts visible to the current user.\n\n"
            "- Patients see posts marked as visible to patients.\n"
            "- Doctors see posts marked as visible to staff.\n\n"
            "Optional: Filter posts by category slug using `?category=<slug>`."
        ),
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter posts by category slug (e.g., 'cardiology')",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="List of published posts",
                examples={
                    "application/json": [
                        {"id": 1, "title": "Heart Health Basics", "author": "Dr. John Doe", "category": "Cardiology"},
                        {"id": 2, "title": "Managing Anxiety", "author": "Dr. Emily Smith", "category": "Mental Health"}
                    ]
                }
            )
        },
        tags=['Posts']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        category_slug = self.request.query_params.get('category', None)
        return get_community_posts(user=self.request.user, category_slug=category_slug)

class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Create a new community post",
        operation_description="Allows doctors to create posts (supports image upload).",
        request_body=PostCreateSerializer,
        consumes=['multipart/form-data'],
        responses={
            201: openapi.Response(
                description="Post created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Post created successfully",
                        "post": {
                            "id": 1,
                            "title": "Heart Health Basics",
                            "status": "published"
                        }
                    }
                }
            )
        },
        tags=['Posts']
    )

    def post(self, request):
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {"error": "Only doctors can create posts"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from rest_framework.exceptions import ValidationError
        try:
            post = create_community_post(author=request.user, data=request.data)
            # We need to serialize the post object for the response
            # PostCreateSerializer works for create, but maybe we want the data back
            return Response({
                "success": True,
                "message": "Post created successfully",
                "post": PostCreateSerializer(post).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get post details by slug",
        operation_description="Fetch full details for a published post. Automatically increments view count.",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the post", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Post details",
                examples={
                    "application/json": {
                        "id": 5,
                        "title": "Understanding Mental Health",
                        "content": "In-depth discussion...",
                        "views_count": 32
                    }
                }
            ),
            404: "Post not found"
        },
        tags=['Posts']
    )
    def get(self, request, slug):
        post = get_post_detail(slug=slug)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
            
        increment_post_view_count(post=post)
        serializer = PostDetailSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete a post",
        operation_description="Delete a post owned by the logged-in doctor.",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the post to delete", type=openapi.TYPE_STRING)
        ],
        responses={
            204: "Post deleted successfully",
            403: "You can only delete your own posts",
            404: "Post not found"
        },
        tags=['Posts']
    )
    def delete(self, request, slug):
        if not hasattr(request.user, 'doctor_profile'):
            return Response(
                {"error": "Only doctors can delete posts"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post = Post.objects.filter(slug=slug).first()
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if post.author != request.user:
            return Response(
                {"error": "You can only delete your own posts"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        delete_community_post(post=post)
        return Response(
            {"message": "Post deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Like or unlike a post",
        operation_description="Toggle like status for a given post. If already liked, it will unlike the post.",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the post", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Like toggled",
                examples={
                    "application/json": {"message": "Post liked", "total_likes": 15, "is_liked": True}
                }
            ),
            404: "Post not found"
        },
        tags=['Posts']
    )
    def post(self, request, slug):
        post = get_post_detail(slug=slug)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
            
        result = toggle_post_like(post=post, user=request.user)
        return Response(result, status=status.HTTP_200_OK)
        
class CommentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    @swagger_auto_schema(
        operation_summary="List comments for a post",
        operation_description="Fetch all approved top-level comments (with nested replies) for a given post.",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the post", type=openapi.TYPE_STRING)
        ],
        responses={200: CommentSerializer(many=True)},
        tags=['Comments']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return get_post_comments(post_slug=slug)


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Add a comment to a post",
        operation_description="Allows users to comment on a post or reply to an existing comment by providing `parent` ID.",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_PATH, description="Slug of the post", type=openapi.TYPE_STRING)
        ],
        request_body=CommentCreateSerializer,
        responses={
            201: openapi.Response(
                description="Comment created successfully",
                examples={
                    "application/json": {"id": 1, "content": "Great post!", "author": "john_doe"}
                }
            ),
            400: "Invalid input",
            404: "Post not found"
        },
        tags=['Comments']
    )
    def post(self, request, slug):
        post = get_post_detail(slug=slug)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
            
        from rest_framework.exceptions import ValidationError
        try:
            comment = create_post_comment(post=post, author=request.user, data=request.data)
            return Response(CommentCreateSerializer(comment).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

class MyPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer

    @swagger_auto_schema(
        operation_summary="List my posts",
        operation_description="Retrieve all posts authored by the currently authenticated user (any status).",
        responses={200: PostListSerializer(many=True)},
        tags=['Posts']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return get_user_posts(user=self.request.user)
