from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserSettings

@receiver(post_save, sender=CustomUser)
def create_user_settings(sender, instance, created, **kwargs):
    """إنشاء إعدادات المستخدم تلقائياً عند إنشاء مستخدم جديد"""
    if created:
        UserSettings.objects.get_or_create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_settings(sender, instance, **kwargs):
    """تأكد من أن الإعدادات موجودة"""
    try:
        instance.user_settings.save()
    except UserSettings.DoesNotExist:
        UserSettings.objects.create(user=instance)
