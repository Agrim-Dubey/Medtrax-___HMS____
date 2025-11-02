from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
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


class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PostListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer
    
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
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
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
    
    def delete(self, request, slug):
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
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
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
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        try:
            post = Post.objects.get(slug=slug, status='published')
            return post.comments.filter(is_approved=True, parent=None)
        except Post.DoesNotExist:
            return Comment.objects.none()


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
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
    permission_classes = [IsAuthenticated]
    serializer_class = PostListSerializer
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}