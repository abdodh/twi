from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm
from accounts.models import CustomUser
from friends.models import Follow



from django.db.models import Q

@login_required
def search_view(request):
    """صفحة البحث"""
    query = request.GET.get('q', '').strip()
    results = {
        'users': [],
        'posts': [],
        'hashtags': []
    }
    
    if query:
        # البحث عن المستخدمين
        results['users'] = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(bio__icontains=query)
        )[:10]
        
        # البحث عن المنشورات
        results['posts'] = Post.objects.filter(
            Q(content__icontains=query)
        ).select_related('user').order_by('-created_at')[:20]
        
        # البحث عن الهاشتاجات (إذا بدأ البحث بـ #)
        if query.startswith('#'):
            hashtag = query[1:]  # إزالة #
            results['posts'] = Post.objects.filter(
                content__icontains=f'#{hashtag}'
            ).select_related('user').order_by('-created_at')[:20]
    
    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'results_count': sum(len(v) for v in results.values())
    })

############################
"""
@login_required
def home_view(request):
   
    posts = Post.objects.all().order_by('-created_at')[:20]
    
    # إضافة بيانات لكل منشور
    for post in posts:
        post.user_has_liked = Like.objects.filter(post=post, user=request.user).exists()
        post.comments = Comment.objects.filter(post=post, parent=None)[:5]
        for comment in post.comments:
            comment.user_has_liked = Like.objects.filter(comment=comment, user=request.user).exists()
            comment.replies_count = Comment.objects.filter(parent=comment).count()
    
    # إحصائيات المستخدم
    user_stats = {
        'posts_count': Post.objects.filter(user=request.user).count(),
        'following_count': Follow.objects.filter(follower=request.user).count(),
        'followers_count': Follow.objects.filter(following=request.user).count(),
    }
    
    return render(request, 'home.html', {
        'posts': posts,
        'user': request.user,
        'user_stats': user_stats,
    })
"""
############
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count, Q
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm, EditPostForm
from accounts.models import CustomUser
from friends.models import Follow

@login_required
def home_view(request):

    try:
        # حاول استخدام is_deleted إذا كان موجوداً
        posts = Post.objects.filter(is_deleted=False).order_by('-created_at')[:20]
    except:
        # إذا لم يكن الحقل موجوداً، استخدم جميع المنشورات
        posts = Post.objects.all().order_by('-created_at')[:20]
    
    # الحصول على جميع التعليقات والـ likes دفعة واحدة لتحسين الأداء
    post_ids = [post.id for post in posts]
    
    # الحصول على likes للمنشورات
    post_likes = Like.objects.filter(
        post_id__in=post_ids,
        user=request.user
    ).values_list('post_id', flat=True)
    
    post_likes_dict = {post_id: True for post_id in post_likes}
    
    # الحصول على التعليقات للمنشورات
    comments = Comment.objects.filter(
        post_id__in=post_ids,
        parent=None
    ).order_by('created_at')[:5]
    
    # تنظيم التعليقات حسب المنشور
    comments_by_post = {}
    for comment in comments:
        if comment.post_id not in comments_by_post:
            comments_by_post[comment.post_id] = []
        comments_by_post[comment.post_id].append(comment)
    
    # الحصول على likes للتعليقات
    comment_ids = [comment.id for comment in comments]
    comment_likes = Like.objects.filter(
        comment_id__in=comment_ids,
        user=request.user
    ).values_list('comment_id', flat=True)
    
    comment_likes_dict = {comment_id: True for comment_id in comment_likes}
    
    # إضافة بيانات لكل منشور
    for post in posts:
        # إعجابات المنشور
        post.user_has_liked = post.id in post_likes_dict
        
        # التعليقات
        post.comments_list = comments_by_post.get(post.id, [])
        
        # إضافة بيانات للتعليقات
        for comment in post.comments_list:
            comment.user_has_liked = comment.id in comment_likes_dict
            comment.replies_count = Comment.objects.filter(parent=comment).count()
        
        # صلاحيات التعديل والحذف
        post.can_edit = post.can_edit(request.user) if hasattr(post, 'can_edit') else post.user == request.user
        post.can_delete = post.can_delete(request.user) if hasattr(post, 'can_delete') else post.user == request.user or request.user.is_staff
    
    # إحصائيات المستخدم
    try:
        user_stats = {
            'posts_count': Post.objects.filter(user=request.user, is_deleted=False).count(),
            'following_count': Follow.objects.filter(follower=request.user).count(),
            'followers_count': Follow.objects.filter(following=request.user).count(),
        }
    except:
        user_stats = {
            'posts_count': Post.objects.filter(user=request.user).count(),
            'following_count': Follow.objects.filter(follower=request.user).count(),
            'followers_count': Follow.objects.filter(following=request.user).count(),
        }
    
    return render(request, 'home.html', {
        'posts': posts,
        'user': request.user,
        'user_stats': user_stats,
    })
    
#############

@login_required
def edit_post(request, post_id):
    """تعديل منشور"""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    
    # التحقق من صلاحية المستخدم
    if not post.can_edit(request.user):
        return HttpResponseForbidden("ليس لديك صلاحية تعديل هذا المنشور")
    
    if request.method == 'POST':
        form = EditPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            edited_post = form.save(commit=False)
            edited_post.is_edited = True
            edited_post.save()
            
            messages.success(request, 'تم تعديل التغريدة بنجاح')
            return redirect('home')
    else:
        form = EditPostForm(instance=post)
    
    return render(request, 'posts/edit.html', {
        'form': form,
        'post': post,
    })

@login_required
def delete_post(request, post_id):
    """حذف منشور"""
    post = get_object_or_404(Post, id=post_id)
    
    # التحقق من صلاحية المستخدم
    if not post.can_delete(request.user):
        return HttpResponseForbidden("ليس لديك صلاحية حذف هذا المنشور")
    
    if request.method == 'POST':
        post.soft_delete()
        messages.success(request, 'تم حذف التغريدة بنجاح')
        return redirect('home')
    
    return render(request, 'posts/delete_confirm.html', {
        'post': post,
    })

@login_required
def restore_post(request, post_id):
    """استعادة منشور محذوف"""
    post = get_object_or_404(Post, id=post_id, is_deleted=True)
    
    # التحقق من صلاحية المستخدم
    if not post.can_edit(request.user):
        return HttpResponseForbidden("ليس لديك صلاحية استعادة هذا المنشور")
    
    post.restore()
    messages.success(request, 'تم استعادة التغريدة بنجاح')
    return redirect('home')

@login_required
def permanent_delete_post(request, post_id):
    """حذف نهائي للمنشور"""
    post = get_object_or_404(Post, id=post_id)
    
    # التحقق من صلاحية المستخدم
    if not post.can_delete(request.user):
        return HttpResponseForbidden("ليس لديك صلاحية حذف هذا المنشور")
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'تم الحذف النهائي للتغريدة')
        return redirect('home')
    
    return render(request, 'posts/permanent_delete_confirm.html', {
        'post': post,
    })

###########
@login_required
def create_post(request):
    """إنشاء منشور جديد"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'تم نشر التغريدة بنجاح')
        else:
            messages.error(request, 'حدث خطأ أثناء نشر التغريدة')
    return redirect('home')

@login_required
def like_post(request, post_id):
    """الإعجاب/إلغاء الإعجاب بمنشور"""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        like.delete()
        post.likes_count -= 1
        action = 'unliked'
    else:
        post.likes_count += 1
        action = 'liked'
    
    post.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'action': action,
            'likes_count': post.likes_count,
        })
    
    messages.info(request, f'تم {action} المنشور')
    return redirect('home')

@login_required
def post_detail(request, post_id):
    """تفاصيل المنشور مع التعليقات"""
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at')
    
    # إضافة بيانات لكل تعليق
    for comment in comments:
        comment.user_has_liked = Like.objects.filter(comment=comment, user=request.user).exists()
        comment.replies_list = Comment.objects.filter(parent=comment).order_by('created_at')
        for reply in comment.replies_list:
            reply.user_has_liked = Like.objects.filter(comment=reply, user=request.user).exists()
    
    post.user_has_liked = Like.objects.filter(post=post, user=request.user).exists()
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            
            post.comments_count += 1
            post.save()
            
            messages.success(request, 'تم إضافة التعليق بنجاح')
            return redirect('post_detail', post_id=post_id)
    
    return render(request, 'posts/detail.html', {
        'post': post,
        'comments': comments,
        'form': CommentForm(),
    })

@login_required
def add_comment(request, post_id):
    """إضافة تعليق جديد"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            
            post.comments_count += 1
            post.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'content': comment.content,
                        'user': {
                            'username': comment.user.username,
                            'profile_image': comment.user.profile_image.url if comment.user.profile_image else '',
                        },
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'likes_count': 0,
                    }
                })
            
            messages.success(request, 'تم إضافة التعليق بنجاح')
    
    return redirect('post_detail', post_id=post_id)

@login_required
def reply_comment(request, comment_id):
    """الرد على تعليق"""
    if request.method == 'POST':
        parent_comment = get_object_or_404(Comment, id=comment_id)
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = parent_comment.post
            comment.user = request.user
            comment.parent = parent_comment  # هذا هو التعديل الصحيح
            comment.save()
            
            parent_comment.post.comments_count += 1
            parent_comment.post.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'content': comment.content,
                        'user': {
                            'username': comment.user.username,
                            'profile_image': comment.user.profile_image.url if comment.user.profile_image else '',
                        },
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'likes_count': 0,
                        'is_reply': True,
                    }
                })
            
            messages.success(request, 'تم إضافة الرد بنجاح')
    
    return redirect('post_detail', post_id=parent_comment.post.id)

@login_required
def like_comment(request, comment_id):
    """الإعجاب/إلغاء الإعجاب بتعليق"""
    comment = get_object_or_404(Comment, id=comment_id)
    like, created = Like.objects.get_or_create(comment=comment, user=request.user)
    
    if not created:
        like.delete()
        comment.likes_count -= 1
        action = 'unliked'
    else:
        comment.likes_count += 1
        action = 'liked'
    
    comment.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'action': action,
            'likes_count': comment.likes_count,
        })
    
    messages.info(request, f'تم {action} التعليق')
    return redirect('post_detail', post_id=comment.post.id)

@login_required
def post_likes(request, post_id):
    """قائمة معجبي المنشور"""
    post = get_object_or_404(Post, id=post_id)
    likes = Like.objects.filter(post=post).select_related('user')
    
    return render(request, 'posts/likes.html', {
        'post': post,
        'likes': likes,
    })

@login_required
def comment_likes(request, comment_id):
    """قائمة معجبي التعليق"""
    comment = get_object_or_404(Comment, id=comment_id)
    likes = Like.objects.filter(comment=comment).select_related('user')
    
    return render(request, 'comments/likes.html', {
        'comment': comment,
        'likes': likes,
    })

@login_required
def delete_comment(request, comment_id):
    """حذف تعليق"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # التحقق من صلاحية المستخدم
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية حذف هذا التعليق')
        return redirect('post_detail', post_id=comment.post.id)
    
    post = comment.post
    comment.delete()
    
    # تحديث عدد التعليقات
    post.comments_count = Comment.objects.filter(post=post).count()
    post.save()
    
    messages.success(request, 'تم حذف التعليق بنجاح')
    return redirect('post_detail', post_id=post.id)
    
@login_required
def edit_comment(request, comment_id):
    """تعديل تعليق"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # التحقق من صلاحية المستخدم
    if comment.user != request.user:
        return HttpResponseForbidden("ليس لديك صلاحية تعديل هذا التعليق")
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment.content = content
            comment.is_edited = True
            comment.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'content': comment.content,
                    'is_edited': comment.is_edited,
                })
            
            messages.success(request, 'تم تعديل التعليق بنجاح')
        else:
            messages.error(request, 'محتوى التعليق مطلوب')
    
    return redirect('post_detail', post_id=comment.post.id)
