from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import CustomUser
from .models import Friendship, Follow
from django.db.models import Count


  

@login_required
def toggle_follow(request, username):
    """المتابعة/إلغاء المتابعة"""
    user_to_follow = get_object_or_404(CustomUser, username=username)
    
    if request.user == user_to_follow:
        messages.error(request, 'لا يمكنك متابعة نفسك')
        return redirect('profile_with_username', username=username)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if not created:
        follow.delete()
        request.user.following_count -= 1
        user_to_follow.followers_count -= 1
        action = 'إلغاء المتابعة'
    else:
        request.user.following_count += 1
        user_to_follow.followers_count += 1
        action = 'المتابعة'
    
    request.user.save()
    user_to_follow.save()
    
    messages.success(request, f'تم {action} @{username}')
    return redirect('profile_with_username', username=username)
@login_required
def friends_list(request):
    """قائمة الأصدقاء"""
    # الحصول على جميع الصداقات المقبولة
    friendships = Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    ).select_related('from_user', 'to_user')
    
    # تجهيز قائمة الأصدقاء
    friends = []
    for friendship in friendships:
        if friendship.from_user == request.user:
            friend = friendship.to_user
        else:
            friend = friendship.from_user
        
        # الحصول على آخر منشور للصديق
        last_post = friend.posts.filter(is_deleted=False).first()
        
        friends.append({
            'user': friend,
            'friendship': friendship,
            'last_post': last_post,
            'is_following': Follow.objects.filter(
                follower=request.user,
                following=friend
            ).exists()
        })
    
    return render(request, 'friends/list.html', {
        'friends': friends,
        'page_title': 'قائمة الأصدقاء'
    })

@login_required
def friend_requests(request):
    """طلبات الصداقة الواردة"""
    # طلبات الصداقة الواردة (المستخدم الحالي هو المستقبل)
    incoming_requests = Friendship.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')
    
    # طلبات الصداقة الصادرة (المستخدم الحالي هو المرسل)
    outgoing_requests = Friendship.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user')
    
    return render(request, 'friends/requests.html', {
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'page_title': 'طلبات الصداقة'
    })

@login_required
def send_friend_request(request, username):
    """إرسال طلب صداقة"""
    user_to_request = get_object_or_404(CustomUser, username=username)
    
    if request.user == user_to_request:
        messages.error(request, 'لا يمكنك إرسال طلب صداقة لنفسك')
        return redirect('profile_with_username', username=username)
    
    # التحقق إذا كان هناك طلب صداقة موجود بالفعل
    existing_request = Friendship.objects.filter(
        Q(from_user=request.user, to_user=user_to_request) |
        Q(from_user=user_to_request, to_user=request.user)
    ).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            if existing_request.from_user == request.user:
                messages.info(request, 'لقد أرسلت طلب صداقة بالفعل لهذا المستخدم')
            else:
                messages.info(request, 'لديك طلب صداقة من هذا المستخدم')
        elif existing_request.status == 'accepted':
            messages.info(request, 'أنتما أصدقاء بالفعل')
        elif existing_request.status == 'rejected':
            messages.info(request, 'تم رفض طلب الصداقة سابقاً')
        elif existing_request.status == 'blocked':
            messages.info(request, 'هذا المستخدم محظور')
    else:
        # إنشاء طلب صداقة جديد
        Friendship.objects.create(
            from_user=request.user,
            to_user=user_to_request,
            status='pending'
        )
        messages.success(request, f'تم إرسال طلب صداقة إلى @{username}')
    
    return redirect('profile_with_username', username=username)

@login_required
def accept_friend_request(request, request_id):
    """قبول طلب صداقة"""
    friend_request = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    
    if friend_request.status == 'pending':
        friend_request.status = 'accepted'
        friend_request.save()
        messages.success(request, f'تم قبول طلب صداقة من @{friend_request.from_user.username}')
    
    return redirect('friend_requests')

@login_required
def reject_friend_request(request, request_id):
    """رفض طلب صداقة"""
    friend_request = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    
    if friend_request.status == 'pending':
        friend_request.status = 'rejected'
        friend_request.save()
        messages.info(request, f'تم رفض طلب صداقة من @{friend_request.from_user.username}')
    
    return redirect('friend_requests')

@login_required
def cancel_friend_request(request, request_id):
    """إلغاء طلب صداقة مرسل"""
    friend_request = get_object_or_404(Friendship, id=request_id, from_user=request.user)
    
    if friend_request.status == 'pending':
        friend_request.delete()
        messages.info(request, f'تم إلغاء طلب الصداقة إلى @{friend_request.to_user.username}')
    
    return redirect('friend_requests')

@login_required
def remove_friend(request, username):
    """إزالة صديق"""
    friend = get_object_or_404(CustomUser, username=username)
    
    # البحث عن علاقة الصداقة
    friendship = Friendship.objects.filter(
        Q(from_user=request.user, to_user=friend, status='accepted') |
        Q(from_user=friend, to_user=request.user, status='accepted')
    ).first()
    
    if friendship:
        friendship.delete()
        messages.success(request, f'تمت إزالة @{username} من قائمة أصدقائك')
    else:
        messages.error(request, 'لا توجد صداقة مع هذا المستخدم')
    
    return redirect('friends_list')

@login_required
def block_user(request, username):
    """حظر مستخدم"""
    user_to_block = get_object_or_404(CustomUser, username=username)
    
    if request.user == user_to_block:
        messages.error(request, 'لا يمكنك حظر نفسك')
        return redirect('profile_with_username', username=username)
    
    # البحث عن أي علاقة صداقة موجودة
    friendship = Friendship.objects.filter(
        Q(from_user=request.user, to_user=user_to_block) |
        Q(from_user=user_to_block, to_user=request.user)
    ).first()
    
    if friendship:
        friendship.status = 'blocked'
        friendship.save()
    else:
        Friendship.objects.create(
            from_user=request.user,
            to_user=user_to_block,
            status='blocked'
        )
    
    messages.success(request, f'تم حظر @{username}')
    return redirect('profile_with_username', username=username)

@login_required
def unblock_user(request, username):
    """إلغاء حظر مستخدم"""
    user_to_unblock = get_object_or_404(CustomUser, username=username)
    
    friendship = Friendship.objects.filter(
        from_user=request.user,
        to_user=user_to_unblock,
        status='blocked'
    ).first()
    
    if friendship:
        friendship.delete()
        messages.success(request, f'تم إلغاء حظر @{username}')
    else:
        messages.error(request, 'هذا المستخدم غير محظور')
    
    return redirect('profile_with_username', username=username)
