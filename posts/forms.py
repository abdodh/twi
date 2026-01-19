from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'ما الذي يدور في ذهنك؟'
        }),
        required=True,
        label=''
    )
    
    class Meta:
        model = Post
        fields = ['content', 'image', 'video']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'video/*'
            }),
        }

class EditPostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-3 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'ما الذي يدور في ذهنك؟'
        }),
        required=True,
        label='محتوى التغريدة'
    )
    
    remove_image = forms.BooleanField(
        required=False,
        label='إزالة الصورة',
        widget=forms.CheckboxInput(attrs={
            'class': 'ml-2'
        })
    )
    
    remove_video = forms.BooleanField(
        required=False,
        label='إزالة الفيديو',
        widget=forms.CheckboxInput(attrs={
            'class': 'ml-2'
        })
    )
    
    class Meta:
        model = Post
        fields = ['content', 'image', 'video']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'accept': 'video/*'
            }),
        }
    
    def save(self, commit=True):
        post = super().save(commit=False)
        
        # إزالة الصورة إذا طلب المستخدم
        if self.cleaned_data.get('remove_image'):
            post.image.delete(save=False)
            post.image = None
        
        # إزالة الفيديو إذا طلب المستخدم
        if self.cleaned_data.get('remove_video'):
            post.video.delete(save=False)
            post.video = None
        
        if commit:
            post.save()
        
        return post

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'أضف تعليقاً...'
        }),
        required=True,
        label=''
    )
    
    class Meta:
        model = Comment
        fields = ['content']
"""
from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'ما الذي يدور في ذهنك؟'
        }),
        required=True,
        label=''
    )
    
    class Meta:
        model = Post
        fields = ['content', 'image', 'video']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'video/*'
            }),
        }

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'أضف تعليقاً...'
        }),
        required=True,
        label=''
    )
    
    class Meta:
        model = Comment
        fields = ['content']
"""
