
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    bio = models.TextField(max_length=500, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    website = models.URLField(blank=True, default='')
    birth_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png')
    cover_image = models.ImageField(upload_to='cover_pics/', default='cover_pics/default.png')
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.username
    @property
    def settings(self):
        """Property للوصول إلى إعدادات المستخدم"""
        try:
            return self.user_settings
        except UserSettings.DoesNotExist:
            # إذا لم تكن الإعدادات موجودة، قم بإنشائها
            settings = UserSettings.objects.create(user=self)
            return settings
    
    def save(self, *args, **kwargs):
        # تأكد من وجود الإعدادات عند حفظ المستخدم
        super().save(*args, **kwargs)
        if not hasattr(self, 'user_settings'):
            UserSettings.objects.create(user=self)
    @property
    def posts(self):
        return self.posts_set.all()
    
    @property
    def following(self):
        return self.follower.all()
    
    @property
    def followers(self):
        return self.following.all()
    
    @property
    def likes_count(self):
        return self.likes.count()

class UserSettings(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_settings')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    private_account = models.BooleanField(default=False)
    show_activity_status = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    theme = models.CharField(max_length=20, default='light')
    
    def __str__(self):
        return f"Settings for {self.user.username}"

# إشارة لإنشاء UserSettings تلقائياً عند إنشاء مستخدم
@receiver(post_save, sender=CustomUser)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_settings(sender, instance, **kwargs):
    # تأكد من أن الإعدادات موجودة
    if not hasattr(instance, 'user_settings'):
        UserSettings.objects.create(user=instance)
    instance.user_settings.save()
