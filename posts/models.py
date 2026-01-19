from django.db import models
from accounts.models import CustomUser

import re 

class Post(models.Model):
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=280)
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    video = models.FileField(upload_to='post_videos/', null=True, blank=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False) 
    
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        # حفظ المنشور أولاً
        super().save(*args, **kwargs)
        
        # استخراج الهاشتاجات من المحتوى
        hashtags = re.findall(r'#(\w+)', self.content)
        
        for tag_name in hashtags:
            hashtag, created = Hashtag.objects.get_or_create(
                name=tag_name.lower()
            )
            
            if self not in hashtag.posts.all():
                hashtag.posts.add(self)
                hashtag.usage_count += 1
                hashtag.save()
    def can_edit(self, user):
        """التحقق من إمكانية تعديل التغريدة"""
        return user == self.user
    
    def can_delete(self, user):
        """التحقق من إمكانية حذف التغريدة"""
        return user == self.user or user.is_staff
    
    def soft_delete(self):
        """حذف ناعم"""
        self.is_deleted = True
        self.save()
    
    def restore(self):
        """استعادة التغريدة"""
        self.is_deleted = False
        self.save()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_comments')
    content = models.TextField(max_length=280)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on post #{self.post.id}"
    
    @property
    def is_reply(self):
        return self.parent is not None

class Like(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ['user', 'post'],
            ['user', 'comment']
        ]
    
    def __str__(self):
        if self.post:
            return f"{self.user.username} liked post #{self.post.id}"
        return f"{self.user.username} liked comment #{self.comment.id}"
        
class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    posts = models.ManyToManyField(Post, related_name='hashtags', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    usage_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"#{self.name}"
    
    class Meta:
        ordering = ['-usage_count']
