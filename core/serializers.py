from rest_framework import serializers
from accounts.models import CustomUser, UserSettings
from posts.models import Post, Comment, Like
from friends.models import Friendship, Follow

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['email_notifications', 'push_notifications', 
                 'private_account', 'show_activity_status', 
                 'language', 'theme']
        read_only_fields = fields

class UserSerializer(serializers.ModelSerializer):
    user_settings = UserSettingsSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'bio', 'location', 'website', 'profile_image', 
                 'cover_image', 'followers_count', 'following_count', 
                 'is_private', 'created_at', 'user_settings']
        read_only_fields = ['followers_count', 'following_count', 'created_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # إضافة التوافق مع الاسم 'settings'
        representation['settings'] = representation.get('user_settings', {})
        return representation

class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    liked = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    shares_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'post_type', 'image', 'video',
                 'likes_count', 'comments_count', 'shares_count', 
                 'created_at', 'updated_at', 'is_edited', 'liked']
        read_only_fields = ['created_at', 'updated_at', 'is_edited']
    
    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'content', 'parent', 
                 'likes_count', 'created_at', 'updated_at', 'replies', 'liked']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []
    
    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(comment=obj, user=request.user).exists()
        return False

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'comment', 'created_at']
        read_only_fields = ['created_at']

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['created_at']

class FriendshipSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'status', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
