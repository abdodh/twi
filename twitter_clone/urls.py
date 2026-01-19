from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from posts.views import search_ajax



 
from django.contrib.auth import views as auth_views

# استيراد الـ views
from posts.views import (
    home_view, create_post, like_post, post_detail,
    add_comment, reply_comment, like_comment,
    post_likes, comment_likes, delete_comment,
    edit_post, delete_post, search_view
)
from accounts.views import (
    profile_view, profile_settings, account_settings,
    security_settings, logout_view, register_view
)


from friends.views import (
    friends_list, friend_requests, send_friend_request,
    accept_friend_request, reject_friend_request, cancel_friend_request,
    remove_friend, block_user, unblock_user
)
from friends.views import toggle_follow 
########"" followers_list,












# استيراد الـ views
 

from core.api_views import (
    register_api, login_api, logout_api, current_user_api,
    UserViewSet, PostViewSet, CommentViewSet,
    FriendshipViewSet, FollowViewSet, FeedView, SearchView
)

# إنشاء Router للـ API
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'friendships', FriendshipViewSet, basename='friendship')
router.register(r'follows', FollowViewSet, basename='follow')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/register/', register_api, name='api_register'),
    path('api/login/', login_api, name='api_login'),
    path('api/logout/', logout_api, name='api_logout'),
    path('api/current-user/', current_user_api, name='api_current_user'),
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),
    
    # API Router
    path('api/', include(router.urls)),
    
    # Special API Endpoints
    path('api/feed/', FeedView.as_view(), name='api_feed'),
    path('api/search/', SearchView.as_view(), name='api_search'),
    
    # DRF Authentication (لـ browsable API)
    path('api-auth/', include('rest_framework.urls')),
    
    # Frontend Views (الواجهة الحالية)
    path('', include('posts.urls')),
    path('accounts/', include('accounts.urls')),
    
    path('', home_view, name='home'),
    path('create-post/', create_post, name='create_post'),
    path('like-post/<int:post_id>/', like_post, name='like_post'),
    path('post/<int:post_id>/', post_detail, name='post_detail'),
    path('post/<int:post_id>/likes/', post_likes, name='post_likes'),
    
    # البحث
      path('friends/', friends_list, name='friends_list'),
    path('friends/requests/', friend_requests, name='friend_requests'),
    path('friends/send-request/<str:username>/', send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', accept_friend_request, name='accept_friend_request'),
    path('friends/reject/<int:request_id>/', reject_friend_request, name='reject_friend_request'),
    path('friends/cancel/<int:request_id>/', cancel_friend_request, name='cancel_friend_request'),
    path('friends/remove/<str:username>/', remove_friend, name='remove_friend'),
    path('friends/block/<str:username>/', block_user, name='block_user'),
    path('friends/unblock/<str:username>/', unblock_user, name='unblock_user'),
    

    
 path('search/', search_view, name='search'),

    path('post/<int:post_id>/comment/', add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reply/', reply_comment, name='reply_comment'),
    path('comment/<int:comment_id>/like/', like_comment, name='like_comment'),
    path('comment/<int:comment_id>/likes/', comment_likes, name='comment_likes'),
    path('comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    
    # تعديل وحذف المنشورات
    path('post/<int:post_id>/edit/', edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', delete_post, name='delete_post'),
    
    # الملف الشخصي
    path('profile/<str:username>/', profile_view, name='profile_with_username'),
    path('profile/', profile_view, name='profile'),
    
    # الإعدادات
    path('settings/profile/', profile_settings, name='profile_settings'),
    path('settings/account/', account_settings, name='account_settings'),
    path('settings/security/', security_settings, name='security_settings'),
    
    # المتابعة
     
    # المتابعة - **هذا هو المسار المطلوب**
    path('follow/<str:username>/', toggle_follow, name='toggle_follow'),
    #path('follow/<str:username>/', toggle_follow, name='toggle_follow'),
    

    path('search/ajax/', search_ajax, name='search_ajax'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
