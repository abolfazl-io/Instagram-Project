# shop1/forms.py
from django import forms
from .models import Post, Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'bio', 'phone', 'image']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # The 'image' field is removed from here
        fields = ['title', 'desc', 'status']