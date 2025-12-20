from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from posts.models import Post, Comment, Like
from friends.models import Friendship, Follow

# استيراد الـ serializers بعد تعريف الـ models
from .serializers import (
    UserSerializer, PostSerializer, CommentSerializer,
    UserSettingsSerializer, FriendshipSerializer
)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_at')
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(content__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(
            post=post, 
            user=request.user
        )
        if not created:
            like.delete()
            post.likes_count -= 1
            liked = False
        else:
            post.likes_count += 1
            liked = True
        post.save()
        return Response({'status': 'liked' if liked else 'unliked', 'liked': liked})
    
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post, user=request.user)
            post.comments_count += 1
            post.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        if not created:
            follow.delete()
            request.user.following_count -= 1
            user_to_follow.followers_count -= 1
            followed = False
        else:
            request.user.following_count += 1
            user_to_follow.followers_count += 1
            followed = True
        
        request.user.save()
        user_to_follow.save()
        return Response({'status': 'followed' if followed else 'unfollowed', 'followed': followed})
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:20]
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        user = self.get_object()
        posts = Post.objects.filter(user=user).order_by('-created_at')
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

class FriendshipViewSet(viewsets.ModelViewSet):
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Friendship.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friendship = self.get_object()
        if friendship.to_user == request.user:
            friendship.status = 'accepted'
            friendship.save()
            return Response({'status': 'accepted'})
        return Response({'status': 'error', 'message': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        friendship = self.get_object()
        if friendship.to_user == request.user:
            friendship.status = 'rejected'
            friendship.save()
            return Response({'status': 'rejected'})
        return Response({'status': 'error', 'message': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

# Views للتصديق البسيط
@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({
            'status': 'success', 
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        })
    return Response({
        'status': 'error', 
        'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'status': 'success'})

@api_view(['POST'])
def register_view(request):
    from django.contrib.auth.forms import UserCreationForm
    from accounts.forms import CustomUserCreationForm
    
    form = CustomUserCreationForm(request.data)
    if form.is_valid():
        user = form.save()
        
        # تسجيل دخول المستخدم تلقائياً
        login(request, user)
        
        # إرجاع بيانات المستخدم
        serializer = UserSerializer(user)
        return Response({
            'status': 'success',
            'user': serializer.data
        })
    
    return Response({
        'status': 'error',
        'errors': form.errors
    }, status=status.HTTP_400_BAD_REQUEST)

# View للحصول على المستخدم الحالي
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
