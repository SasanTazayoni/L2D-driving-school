from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import UserProfile
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """
    Creates a custom sign up form for new users signing up.
    """
    first_name = forms.CharField(label="Name", max_length=40)

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Please choose a different username")
        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise ValidationError("First name is required")
        return first_name


class UserProfileForm(forms.ModelForm):
    """
    Establishes a user profile form for editing various details of
    an authenticated user.
    """
    email = forms.EmailField(
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    first_name = forms.CharField(label="Name", max_length=40)

    class Meta:
        model = UserProfile
        fields = [
            'email',
            'first_name',
            'age',
            'occupation',
            'about_me',
            'profile_picture'
        ]
