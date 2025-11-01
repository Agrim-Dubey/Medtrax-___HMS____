from rest_framework import serializers
from .models import Post, Comment, Like, Category, PostImage
from Authapi.models import CustomUser

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'caption', 'uploaded_at']


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'author',
            'author_name',
            'author_role',
            'content',
            'parent',
            'created_at',
            'updated_at',
            'replies'
        ]
        read_only_fields = ['author', 'created_at']
    
    def get_author_name(self, obj):
        try:
            if hasattr(obj.author, 'doctor_profile'):
                return f"Dr. {obj.author.doctor_profile.get_full_name()}"
            elif hasattr(obj.author, 'patient_profile'):
                return obj.author.patient_profile.get_full_name()
        except:
            return obj.author.username
    
    def get_author_role(self, obj):
        return getattr(obj.author, 'role', 'unknown')
    
    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.filter(is_approved=True)
            return CommentSerializer(replies, many=True).data
        return []


class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_likes = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'author',
            'author_name',
            'author_role',
            'category_name',
            'excerpt',
            'featured_image',
            'status',
            'created_at',
            'published_at',
            'views_count',
            'total_likes',
            'total_comments',
            'is_liked'
        ]
    
    def get_author_name(self, obj):
        try:
            if hasattr(obj.author, 'doctor_profile'):
                return f"Dr. {obj.author.doctor_profile.get_full_name()}"
            elif hasattr(obj.author, 'patient_profile'):
                return obj.author.patient_profile.get_full_name()
        except:
            return obj.author.username
    
    def get_author_role(self, obj):
        return getattr(obj.author, 'role', 'unknown')
    
    def get_total_likes(self, obj):
        return obj.likes.count()
    
    def get_total_comments(self, obj):
        return obj.comments.filter(is_approved=True, parent=None).count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False


class PostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'author',
            'author_name',
            'author_role',
            'category',
            'content',
            'excerpt',
            'featured_image',
            'images',
            'status',
            'created_at',
            'updated_at',
            'published_at',
            'views_count',
            'total_likes',
            'is_liked',
            'comments'
        ]
    
    def get_author_name(self, obj):
        try:
            if hasattr(obj.author, 'doctor_profile'):
                return f"Dr. {obj.author.doctor_profile.get_full_name()}"
            elif hasattr(obj.author, 'patient_profile'):
                return obj.author.patient_profile.get_full_name()
        except:
            return obj.author.username
    
    def get_author_role(self, obj):
        return getattr(obj.author, 'role', 'unknown')
    
    def get_total_likes(self, obj):
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False
    
    def get_comments(self, obj):
        comments = obj.comments.filter(is_approved=True, parent=None)
        return CommentSerializer(comments, many=True).data


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            'title',
            'category',
            'content',
            'excerpt',
            'featured_image',
            'status'
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'parent']