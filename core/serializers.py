from rest_framework import serializers
from rest_framework.authtoken.models import Token
from accounts.models import CustomUser, UserSettings
from posts.models import Post, Comment, Like
from friends.models import Friendship, Follow

# تسجيل User
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    token = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'token']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        Token.objects.create(user=user)
        return user
    
    def get_token(self, obj):
        token, created = Token.objects.get_or_create(user=obj)
        return token.key

# تسجيل الدخول
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

# إعدادات المستخدم
class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = '__all__'
        read_only_fields = ['user']

# ملف المستخدم
class UserSerializer(serializers.ModelSerializer):
    settings = UserSettingsSerializer(read_only=True)
    is_following = serializers.SerializerMethodField()
    is_followed_by = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'location', 'website', 'profile_image', 'cover_image',
            'followers_count', 'following_count', 'is_private',
            'created_at', 'settings', 'is_following', 'is_followed_by'
        ]
        read_only_fields = ['followers_count', 'following_count', 'created_at']
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False
    
    def get_is_followed_by(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=obj, following=request.user).exists()
        return False

# منشور مختصر (للقوائم)
class PostListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'post_type', 'image', 'video',
            'likes_count', 'comments_count', 'created_at', 'is_edited', 'liked'
        ]
    
    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False

# منشور كامل
class PostDetailSerializer(PostListSerializer):
    comments = serializers.SerializerMethodField()
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['updated_at', 'comments']
    
    def get_comments(self, obj):
        comments = Comment.objects.filter(post=obj, parent=None)[:10]
        return CommentSerializer(comments, many=True, context=self.context).data

# إنشاء منشور
class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'post_type']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

# تعليق
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'content', 'parent', 'likes_count',
            'created_at', 'updated_at', 'is_edited', 'replies', 'liked'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_edited']
    
    def get_replies(self, obj):
        replies = Comment.objects.filter(parent=obj)[:5]
        return CommentSerializer(replies, many=True, context=self.context).data
    
    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(comment=obj, user=request.user).exists()
        return False

# إعجاب
class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'comment', 'created_at']
        read_only_fields = ['created_at']

# متابعة
class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['created_at']

# صداقة
class FriendshipSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
