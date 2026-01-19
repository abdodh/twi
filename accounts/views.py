from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout as auth_logout
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.db.models import Count  # أضف هذا السطر
from .models import CustomUser
from posts.models import Post, Like
from friends.models import Follow
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login

# بدلاً من:
from django.db.models import Count

# يمكنك استخدام:
# from django.db.models import ... (استيراد ما تحتاجه فقط)
def register_view(request):
    """إنشاء حساب جديد"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # تسجيل دخول المستخدم تلقائياً
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'تم إنشاء حسابك بنجاح!')
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout_view(request):
    """تسجيل الخروج - يدعم GET و POST"""
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect('home')

@login_required
def profile_view(request, username=None):
    """عرض الملف الشخصي"""
    if username:
        user = get_object_or_404(CustomUser, username=username)
    else:
        # إذا لم يتم تحديد username، عرض ملف المستخدم الحالي
        user = request.user
    
    # التحقق إذا كان المستخدم يتابع هذا المستخدم
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    
    # الحصول على المنشورات
    posts = Post.objects.filter(user=user).order_by('-created_at')
    
    # الحصول على الإحصائيات
    stats = {
        'posts_count': posts.count(),
        'following_count': Follow.objects.filter(follower=user).count(),
        'followers_count': Follow.objects.filter(following=user).count(),
    }
    
    # الحصول على المنشورات المعجبة بها
    liked_posts = Post.objects.filter(post_likes__user=user).distinct().order_by('-post_likes__created_at')[:10]
    
    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'posts': posts,
        'liked_posts': liked_posts,
        'stats': stats,
        'is_following': is_following,
        'is_own_profile': user == request.user,
    })

@login_required
def profile_settings(request):
    """إعدادات الملف الشخصي"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.bio = request.POST.get('bio', '')
        user.location = request.POST.get('location', '')
        user.website = request.POST.get('website', '')
        
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        if 'cover_image' in request.FILES:
            user.cover_image = request.FILES['cover_image']
        
        user.save()
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
        return redirect('profile_settings')
    
    return render(request, 'accounts/settings/profile.html')

@login_required
def account_settings(request):
    """إعدادات الحساب"""
    return render(request, 'accounts/settings/account.html')

@login_required
def security_settings(request):
    """إعدادات الأمان"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('security_settings')
        else:
            messages.error(request, 'حدث خطأ. يرجى التحقق من البيانات المدخلة.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/settings/security.html', {
        'form': form,
    })
