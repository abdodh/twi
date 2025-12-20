from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser, UserSettings

##################




class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'example@email.com'
        })
    )
    
    first_name = forms.CharField(
        required=False,
        label='الاسم الأول',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    
    last_name = forms.CharField(
        required=False,
        label='الاسم الأخير',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'placeholder': 'اسم المستخدم'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تخصيص حقول كلمة المرور
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'كلمة المرور'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'تأكيد كلمة المرور'
        })
#############

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'bio', 'location', 'website', 'profile_image', 'cover_image']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border rounded-lg',
                'placeholder': 'أكتب عن نفسك...'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'placeholder': 'المدينة، الدولة'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg',
                'placeholder': 'https://example.com'
            }),
        }

class SettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['email_notifications', 'push_notifications', 'private_account', 'show_activity_status', 'language', 'theme']
        widgets = {
            'language': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'theme': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }
        labels = {
            'email_notifications': 'إشعارات البريد الإلكتروني',
            'push_notifications': 'إشعارات الدفع',
            'private_account': 'حساب خاص',
            'show_activity_status': 'إظهار حالة النشاط',
            'language': 'اللغة',
            'theme': 'السمة',
        }
