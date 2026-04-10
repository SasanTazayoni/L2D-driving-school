from django import forms
from .models import Comment, Review


class ReviewForm(forms.ModelForm):
    """
    Form for creating or updating a review.
    """
    class Meta:
        model = Review
        fields = ['rating', 'content']


class CommentForm(forms.ModelForm):
    """
    Form for creating a comment on a review.
    """
    class Meta:
        model = Comment
        fields = ('content',)
