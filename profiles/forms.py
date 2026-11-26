from django import forms
from .models import UserProfile
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """
    Adds a required first name to allauth's signup form. allauth itself
    checks (case-insensitively) that the username and email are unique,
    and that an email is given (see ACCOUNT_SIGNUP_FIELDS in settings).
    """
    first_name = forms.CharField(label="Name", max_length=40)


class UserProfileForm(forms.ModelForm):
    """
    Establishes a user profile form for editing various details of
    an authenticated user.
    """
    # Shown for reference only. A disabled field ignores whatever is
    # submitted for it, so the email cannot be changed through this form.
    email = forms.EmailField(disabled=True, required=False)
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
        labels = {'profile_picture': 'Profile picture'}
        # Plain file input: the current picture and a remove option are
        # shown separately in the template.
        widgets = {'profile_picture': forms.FileInput}
