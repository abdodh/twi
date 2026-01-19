from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import CustomUser
from posts.models import Post, Comment, Like
from friends.models import Friendship, Follow
from .serializers import *

# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # تسجيل دخول تلقائي
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'token': token.key,
            'message': 'تم إنشاء الحساب بنجاح'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_api(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'token': token.key,
                'message': 'تم تسجيل الدخول بنجاح'
            })
        
        return Response(
            {'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_api(request):
    logout(request)
    return Response({'message': 'تم تسجيل الخروج بنجاح'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_api(request):
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'created_at', 'followers_count']
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        
        if request.user == user_to_follow:
            return Response(
                {'error': 'لا يمكنك متابعة نفسك'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        return Response({
            'followed': followed,
            'followers_count': user_to_follow.followers_count,
            'following_count': request.user.following_count
        })
    
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        user = self.get_object()
        followers = Follow.objects.filter(following=user).select_related('follower')
        serializer = FollowSerializer(followers, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = self.get_object()
        following = Follow.objects.filter(follower=user).select_related('following')
        serializer = FollowSerializer(following, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        user = self.get_object()
        posts = Post.objects.filter(user=user, is_deleted=False).order_by('-created_at')
        page = self.paginate_queryset(posts)
        
        if page is not None:
            serializer = PostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(is_deleted=False).order_by('-created_at')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['content', 'user__username']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # تصفية حسب المستخدم إذا تم توفير user_id
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # تصفية حسب المستخدمين المتابَعين
        following_only = self.request.query_params.get('following_only')
        if following_only and self.request.user.is_authenticated:
            following_ids = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
            queryset = queryset.filter(user_id__in=following_ids)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        
        if not created:
            like.delete()
            post.likes_count -= 1
            liked = False
        else:
            post.likes_count += 1
            liked = True
        
        post.save()
        
        return Response({
            'liked': liked,
            'likes_count': post.likes_count
        })
    
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        post = self.get_object()
        likes = Like.objects.filter(post=post).select_related('user')
        serializer = LikeSerializer(likes, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(post=post, user=request.user)
            post.comments_count += 1
            post.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

# Comment ViewSet
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # تصفية حسب المنشور إذا تم توفير post_id
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        like, created = Like.objects.get_or_create(comment=comment, user=request.user)
        
        if not created:
            like.delete()
            comment.likes_count -= 1
            liked = False
        else:
            comment.likes_count += 1
            liked = True
        
        comment.save()
        
        return Response({
            'liked': liked,
            'likes_count': comment.likes_count
        })
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        parent_comment = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(post=parent_comment.post, user=request.user, parent=parent_comment)
            parent_comment.post.comments_count += 1
            parent_comment.post.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Friendship ViewSet
class FriendshipViewSet(viewsets.ModelViewSet):
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
        
        if friendship.to_user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية قبول هذا الطلب'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friendship.status = 'accepted'
        friendship.save()
        
        return Response({'status': 'accepted'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        friendship = self.get_object()
        
        if friendship.to_user != request.user:
            return Response(
                {'error': 'ليس لديك صلاحية رفض هذا الطلب'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        friendship.status = 'rejected'
        friendship.save()
        
        return Response({'status': 'rejected'})

# Follow ViewSet
class FollowViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            return Follow.objects.filter(follower_id=user_id).order_by('-created_at')
        
        return Follow.objects.filter(follower=self.request.user).order_by('-created_at')

# Feed View
class FeedView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # الحصول على المنشورات من المستخدمين المتابَعين
        following_ids = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
        
        # إضافة منشورات المستخدم نفسه
        following_ids = list(following_ids) + [self.request.user.id]
        
        return Post.objects.filter(
            user_id__in=following_ids,
            is_deleted=False
        ).order_by('-created_at')

# Search View
class SearchView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        search_type = self.request.query_params.get('type', 'users')
        
        if search_type == 'posts':
            return PostListSerializer
        elif search_type == 'comments':
            return CommentSerializer
        else:
            return UserSerializer
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        search_type = self.request.query_params.get('type', 'users')
        
        if not query:
            return []
        
        if search_type == 'posts':
            return Post.objects.filter(
                Q(content__icontains=query) |
                Q(user__username__icontains=query)
            ).filter(is_deleted=False).order_by('-created_at')
        
        elif search_type == 'comments':
            return Comment.objects.filter(
                Q(content__icontains=query) |
                Q(user__username__icontains=query)
            ).order_by('-created_at')
        
        else:  # users
            return CustomUser.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ).order_by('-date_joined')
