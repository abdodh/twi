from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from posts.models import Post, Hashtag
from friends.models import Follow

@login_required
def search_view(request):
    """صفحة البحث الرئيسية"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # all, users, posts, hashtags
    
    context = {
        'query': query,
        'search_type': search_type,
        'results_count': 0,
    }
    
    if query:
        if search_type in ['all', 'users']:
            context['users'] = search_users(query, request.user)
            context['results_count'] += len(context.get('users', []))
        
        if search_type in ['all', 'posts']:
            context['posts'] = search_posts(query, request.user)
            context['results_count'] += len(context.get('posts', []))
        
        if search_type in ['all', 'hashtags']:
            context['hashtags'] = search_hashtags(query)
            context['results_count'] += len(context.get('hashtags', []))
    
    return render(request, 'search/results.html', context)

def search_users(query, current_user):
    """بحث عن المستخدمين"""
    users = CustomUser.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(bio__icontains=query)
    ).exclude(id=current_user.id)
    
    # إضافة معلومات إضافية لكل مستخدم
    for user in users:
        user.is_following = Follow.objects.filter(
            follower=current_user,
            following=user
        ).exists()
        
        user.posts_count = Post.objects.filter(user=user).count()
        user.followers_count = Follow.objects.filter(following=user).count()
        user.following_count = Follow.objects.filter(follower=user).count()
    
    return users

def search_posts(query, current_user):
    """بحث عن المنشورات"""
    posts = Post.objects.filter(
        Q(content__icontains=query) |
        Q(user__username__icontains=query)
    ).select_related('user').order_by('-created_at')
    
    # إضافة معلومات إضافية لكل منشور
    for post in posts:
        post.user_has_liked = post.post_likes.filter(user=current_user).exists()
        post.comments_count = post.post_comments.count()
    
    return posts

def search_hashtags(query):
    """بحث عن الهاشتاجات"""
    # إذا بدأ البحث بـ #، ابحث عن الهاشتاجات فقط
    if query.startswith('#'):
        hashtag_name = query[1:]  # إزالة #
        return Hashtag.objects.filter(name__icontains=hashtag_name)
    
    # وإلا ابحث في كل مكان
    return Hashtag.objects.filter(name__icontains=query)

@login_required
def autocomplete(request):
    """الاقتراح التلقائي للبحث"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if len(query) >= 2:  # ابدأ الاقتراح بعد حرفين
        # البحث عن المستخدمين
        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:5]
        
        for user in users:
            results.append({
                'type': 'user',
                'username': user.username,
                'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'profile_image': user.profile_image.url if user.profile_image else '',
                'url': f"/profile/{user.username}/"
            })
        
        # البحث عن الهاشتاجات
        hashtags = Hashtag.objects.filter(name__icontains=query)[:5]
        
        for hashtag in hashtags:
            results.append({
                'type': 'hashtag',
                'name': f"#{hashtag.name}",
                'count': hashtag.usage_count,
                'url': f"/search/?q=%23{hashtag.name}&type=hashtags"
            })
    
    return JsonResponse({'results': results})
