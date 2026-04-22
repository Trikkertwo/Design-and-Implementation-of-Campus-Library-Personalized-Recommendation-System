from django import forms
from django.contrib.auth.models import User

from .models import Book, Comment


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    captcha = forms.CharField(max_length=6)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('用户名已存在')
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError('两次密码不一致')
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
    captcha = forms.CharField(max_length=6)


class ResetPasswordForm(forms.Form):
    username = forms.CharField(max_length=50)
    new_password = forms.CharField(widget=forms.PasswordInput)
    captcha = forms.CharField(max_length=6)


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'category', 'publisher', 'publish_year',
            'summary', 'cover_url', 'total_copies', 'available_copies'
        ]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
