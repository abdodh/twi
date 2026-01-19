from django.db import models
from accounts.models import CustomUser
from django.utils import timezone

class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} يتابع {self.following.username}"

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('blocked', 'محظور'),
    ]
    
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendship_requests_sent')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendship_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}: {self.status}"
    
    @property
    def is_accepted(self):
        return self.status == 'accepted'
    
    @property
    def is_pending(self):
        return self.status == 'pending'

class FriendList(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='friend_list')
    friends = models.ManyToManyField(CustomUser, related_name='friend_of', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"قائمة أصدقاء {self.user.username}"
    
    def add_friend(self, user):
        """إضافة صديق إلى القائمة"""
        if not self.is_friend(user):
            self.friends.add(user)
            return True
        return False
    
    def remove_friend(self, user):
        """إزالة صديق من القائمة"""
        if self.is_friend(user):
            self.friends.remove(user)
            return True
        return False
    
    def is_friend(self, user):
        """التحقق إذا كان المستخدم صديقاً"""
        return self.friends.filter(id=user.id).exists()
    
    def get_friends(self):
        """الحصول على جميع الأصدقاء"""
        return self.friends.all()
    
    def get_friends_count(self):
        """عدد الأصدقاء"""
        return self.friends.count()

# إشارات لإنشاء FriendList تلقائياً
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_friend_list(sender, instance, created, **kwargs):
    if created:
        FriendList.objects.create(user=instance)
