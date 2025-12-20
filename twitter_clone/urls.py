from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from friends.views import *
#from search.views import search_view #, autocomplete

from posts.views import search_view

from posts.views import ( 
    edit_post, delete_post, restore_post, permanent_delete_post,edit_comment
)
# استيراد الـ viewsfr
from posts.views import (
    home_view, create_post, like_post, post_detail,
    add_comment, reply_comment, like_comment,
    post_likes, comment_likes, delete_comment
)
from accounts.views import (
    profile_view, profile_settings, account_settings,
    security_settings, logout_view, register_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('post/<int:post_id>/edit/', edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', delete_post, name='delete_post'),
    path('post/<int:post_id>/restore/', restore_post, name='restore_post'),
    path('post/<int:post_id>/permanent-delete/', permanent_delete_post, name='permanent_delete_post'),
    
    # الصفحة الرئيسية والمنشورات
    path('', home_view, name='home'),
    path('create-post/', create_post, name='create_post'),
    path('like-post/<int:post_id>/', like_post, name='like_post'),
    path('post/<int:post_id>/', post_detail, name='post_detail'),
    path('post/<int:post_id>/likes/', post_likes, name='post_likes'),
    
    # التعليقات
    path('post/<int:post_id>/comment/', add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reply/', reply_comment, name='reply_comment'),
    path('comment/<int:comment_id>/like/', like_comment, name='like_comment'),
    path('comment/<int:comment_id>/likes/', comment_likes, name='comment_likes'),
    path('comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    
    # الملف الشخصي
    path('profile/<str:username>/', profile_view, name='profile_with_username'),
    path('profile/', profile_view, name='profile'),
    
    # الإعدادات
    path('settings/profile/', profile_settings, name='profile_settings'),
    path('settings/account/', account_settings, name='account_settings'),
    path('settings/security/', security_settings, name='security_settings'),
    
    # المصادقة
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),  # استخدام view التسجيل الجديد
    
    
    
     # المتابعة
    path('follow/<str:username>/', toggle_follow, name='toggle_follow'),
    
    # الأصدقاء
    path('friend-request/<str:username>/', send_friend_request, name='send_friend_request'),
    path('friend-request/accept/<int:request_id>/', accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', reject_friend_request, name='reject_friend_request'),
    path('friend-request/cancel/<int:request_id>/', cancel_friend_request, name='cancel_friend_request'),
    path('friend/remove/<str:username>/', remove_friend, name='remove_friend'),
    
    # الحظر
    path('block/<str:username>/', block_user, name='block_user'),
    path('unblock/<str:username>/', unblock_user, name='unblock_user'),
    
    # القوائم
    path('friends/', friends_list_view, name='friends_list'),
    path('friends/<str:username>/', friends_list_view, name='friends_list_user'),
    path('friend-requests/', friend_requests_view, name='friend_requests'),
    path('followers/<str:username>/', followers_list_view, name='followers_list'),
    path('following/<str:username>/', following_list_view, name='following_list'),
    path('blocked-users/', blocked_users_view, name='blocked_users'),
    path('suggested-friends/', suggested_friends, name='suggested_friends'),
        path('search/', search_view, name='search'),
            path('comment/<int:comment_id>/edit/', edit_comment, name='edit_comment'),
     #path('search/', search_view, name='search'),
    #path('search/autocomplete/', autocomplete, name='autocomplete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
