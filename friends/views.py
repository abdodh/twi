from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import CustomUser
from .models import Follow, Friendship, FriendList

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
        followed = False
    else:
        request.user.following_count += 1
        user_to_follow.followers_count += 1
        action = 'المتابعة'
        followed = True
    
    request.user.save()
    user_to_follow.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'followed': followed,
            'followers_count': user_to_follow.followers_count,
            'following_count': request.user.following_count,
        })
    
    messages.success(request, f'تم {action} @{username}')
    return redirect('profile_with_username', username=username)

@login_required
def send_friend_request(request, username):
    """إرسال طلب صداقة"""
    to_user = get_object_or_404(CustomUser, username=username)
    
    if request.user == to_user:
        messages.error(request, 'لا يمكنك إرسال طلب صداقة لنفسك')
        return redirect('profile_with_username', username=username)
    
    # التحقق إذا كان هناك طلب صداقة موجود بالفعل
    existing_request = Friendship.objects.filter(
        Q(from_user=request.user, to_user=to_user) |
        Q(from_user=to_user, to_user=request.user)
    ).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            messages.info(request, 'يوجد طلب صداقة قيد الانتظار بالفعل')
        elif existing_request.status == 'accepted':
            messages.info(request, 'أنتم أصدقاء بالفعل')
        elif existing_request.status == 'blocked':
            messages.error(request, 'لا يمكن إرسال طلب صداقة')
        return redirect('profile_with_username', username=username)
    
    # إنشاء طلب صداقة جديد
    friendship = Friendship.objects.create(
        from_user=request.user,
        to_user=to_user,
        status='pending'
    )
    
    messages.success(request, f'تم إرسال طلب صداقة إلى @{username}')
    return redirect('profile_with_username', username=username)

@login_required
def accept_friend_request(request, request_id):
    """قبول طلب صداقة"""
    friendship = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    
    if friendship.status != 'pending':
        messages.error(request, 'طلب الصداقة غير صالح')
        return redirect('friend_requests')
    
    friendship.status = 'accepted'
    friendship.save()
    
    # إضافة إلى قائمة الأصدقاء
    friend_list_from, _ = FriendList.objects.get_or_create(user=friendship.from_user)
    friend_list_to, _ = FriendList.objects.get_or_create(user=friendship.to_user)
    
    friend_list_to.add_friend(friendship.from_user)
    friend_list_from.add_friend(friendship.to_user)
    
    messages.success(request, f'تمت إضافة @{friendship.from_user.username} إلى قائمة أصدقائك')
    return redirect('friend_requests')

@login_required
def reject_friend_request(request, request_id):
    """رفض طلب صداقة"""
    friendship = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    
    if friendship.status != 'pending':
        messages.error(request, 'طلب الصداقة غير صالح')
        return redirect('friend_requests')
    
    friendship.status = 'rejected'
    friendship.save()
    
    messages.info(request, 'تم رفض طلب الصداقة')
    return redirect('friend_requests')

@login_required
def cancel_friend_request(request, request_id):
    """إلغاء طلب صداقة مرسل"""
    friendship = get_object_or_404(Friendship, id=request_id, from_user=request.user)
    
    if friendship.status != 'pending':
        messages.error(request, 'طلب الصداقة غير صالح')
        return redirect('friend_requests')
    
    friendship.delete()
    
    messages.info(request, 'تم إلغاء طلب الصداقة')
    return redirect('friend_requests')

@login_required
def remove_friend(request, username):
    """إزالة صديق"""
    friend = get_object_or_404(CustomUser, username=username)
    
    # إزالة من قائمة الأصدقاء
    try:
        user_friend_list = FriendList.objects.get(user=request.user)
        friend_friend_list = FriendList.objects.get(user=friend)
        
        user_friend_list.remove_friend(friend)
        friend_friend_list.remove_friend(request.user)
        
        # تحديث حالة الصداقة
        Friendship.objects.filter(
            Q(from_user=request.user, to_user=friend) |
            Q(from_user=friend, to_user=request.user)
        ).delete()
        
        messages.success(request, f'تمت إزالة @{username} من قائمة أصدقائك')
    except FriendList.DoesNotExist:
        messages.error(request, 'حدث خطأ أثناء إزالة الصديق')
    
    return redirect('friends_list')

@login_required
def block_user(request, username):
    """حظر مستخدم"""
    user_to_block = get_object_or_404(CustomUser, username=username)
    
    if request.user == user_to_block:
        messages.error(request, 'لا يمكنك حظر نفسك')
        return redirect('profile_with_username', username=username)
    
    # إنشاء أو تحديث سجل الصداقة للحظر
    friendship, created = Friendship.objects.get_or_create(
        from_user=request.user,
        to_user=user_to_block
    )
    friendship.status = 'blocked'
    friendship.save()
    
    # إلغاء المتابعة إن وجدت
    Follow.objects.filter(follower=request.user, following=user_to_block).delete()
    Follow.objects.filter(follower=user_to_block, following=request.user).delete()
    
    # إزالة من قائمة الأصدقاء إن وجد
    try:
        user_friend_list = FriendList.objects.get(user=request.user)
        user_friend_list.remove_friend(user_to_block)
        
        friend_friend_list = FriendList.objects.get(user=user_to_block)
        friend_friend_list.remove_friend(request.user)
    except FriendList.DoesNotExist:
        pass
    
    messages.success(request, f'تم حظر @{username}')
    return redirect('profile_with_username', username=username)

@login_required
def unblock_user(request, username):
    """إلغاء حظر مستخدم"""
    user_to_unblock = get_object_or_404(CustomUser, username=username)
    
    # البحث عن سجل الحظر وحذفه
    Friendship.objects.filter(
        from_user=request.user,
        to_user=user_to_unblock,
        status='blocked'
    ).delete()
    
    messages.success(request, f'تم إلغاء حظر @{username}')
    return redirect('blocked_users')

@login_required
def friend_requests_view(request):
    """عرض طلبات الصداقة"""
    # الطلبات الواردة
    incoming_requests = Friendship.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')
    
    # الطلبات المرسلة
    outgoing_requests = Friendship.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user')
    
    return render(request, 'friends/requests.html', {
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
    })

@login_required
def friends_list_view(request, username=None):
    """عرض قائمة الأصدقاء"""
    if username:
        user = get_object_or_404(CustomUser, username=username)
    else:
        user = request.user
    
    try:
        friend_list = FriendList.objects.get(user=user)
        friends = friend_list.get_friends()
        friends_count = friend_list.get_friends_count()
    except FriendList.DoesNotExist:
        friends = []
        friends_count = 0
    
    return render(request, 'friends/list.html', {
        'profile_user': user,
        'friends': friends,
        'friends_count': friends_count,
        'is_own_profile': user == request.user,
    })

@login_required
def followers_list_view(request, username):
    """عرض قائمة المتابعين"""
    user = get_object_or_404(CustomUser, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    # التحقق من حالة الصداقة والمتابعة
    for follow in followers:
        follow.is_friend = False
        follow.has_pending_request = False
        
        if request.user.is_authenticated:
            # التحقق إذا كان صديقاً
            try:
                user_friend_list = FriendList.objects.get(user=request.user)
                follow.is_friend = user_friend_list.is_friend(follow.follower)
            except FriendList.DoesNotExist:
                pass
            
            # التحقق إذا كان هناك طلب صداقة قيد الانتظار
            follow.has_pending_request = Friendship.objects.filter(
                Q(from_user=request.user, to_user=follow.follower, status='pending') |
                Q(from_user=follow.follower, to_user=request.user, status='pending')
            ).exists()
            
            # التحقق إذا كان المستخدم يتابع هذا المتابِع
            follow.is_following_back = Follow.objects.filter(
                follower=request.user,
                following=follow.follower
            ).exists()
    
    return render(request, 'friends/followers.html', {
        'profile_user': user,
        'followers': followers,
        'is_own_profile': user == request.user,
    })

@login_required
def following_list_view(request, username):
    """عرض قائمة المتابَعين"""
    user = get_object_or_404(CustomUser, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    # التحقق من حالة الصداقة والمتابعة
    for follow in following:
        follow.is_friend = False
        follow.has_pending_request = False
        
        if request.user.is_authenticated:
            # التحقق إذا كان صديقاً
            try:
                user_friend_list = FriendList.objects.get(user=request.user)
                follow.is_friend = user_friend_list.is_friend(follow.following)
            except FriendList.DoesNotExist:
                pass
            
            # التحقق إذا كان هناك طلب صداقة قيد الانتظار
            follow.has_pending_request = Friendship.objects.filter(
                Q(from_user=request.user, to_user=follow.following, status='pending') |
                Q(from_user=follow.following, to_user=request.user, status='pending')
            ).exists()
            
            # التحقق إذا كان المتابَع يتابع المستخدم الحالي
            follow.is_followed_back = Follow.objects.filter(
                follower=follow.following,
                following=user
            ).exists()
    
    return render(request, 'friends/following.html', {
        'profile_user': user,
        'following': following,
        'is_own_profile': user == request.user,
    })

@login_required
def blocked_users_view(request):
    """عرض قائمة المستخدمين المحظورين"""
    blocked_users = Friendship.objects.filter(
        from_user=request.user,
        status='blocked'
    ).select_related('to_user')
    
    return render(request, 'friends/blocked.html', {
        'blocked_users': blocked_users,
    })

@login_required
def suggested_friends(request):
    """اقتراحات أصدقاء"""
    # مستخدمون ليسوا أصدقاء ولا يتابعهم المستخدم الحالي
    user_following = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    
    try:
        user_friend_list = FriendList.objects.get(user=request.user)
        user_friends = user_friend_list.get_friends().values_list('id', flat=True)
    except FriendList.DoesNotExist:
        user_friends = []
    
    # استبعاد المستخدم الحالي وأصدقاؤه والمتابَعين
    excluded_users = list(user_following) + list(user_friends) + [request.user.id]
    
    suggested = CustomUser.objects.exclude(id__in=excluded_users)[:10]
    
    # إضافة معلومات إضافية
    for user in suggested:
        user.is_following = False
        user.has_pending_request = False
    
    return render(request, 'friends/suggested.html', {
        'suggested_users': suggested,
    })
