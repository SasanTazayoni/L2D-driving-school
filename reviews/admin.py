from django.contrib import admin
from .models import Review, Comment
from django_summernote.admin import SummernoteModelAdmin


@admin.register(Review)
class ReviewAdmin(SummernoteModelAdmin):
    """
    Custom admin panel for managing user reviews.
    """
    list_display = ('author', 'rating', 'approved', 'created_on', 'updated_on')
    search_fields = [
        'author__user__first_name', 'author__user__username', 'content'
    ]
    list_filter = ('approved', 'created_on', 'updated_on')
    summernote_fields = ('content',)
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        updated_count = queryset.update(approved=True)
        self.message_user(
            request, f'{updated_count} reviews have been approved.'
            )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Custom admin panel for managing user comments.
    """
    list_display = ('author', 'review', 'approved', 'replied_on', 'updated_on')
    search_fields = [
        'author__user__first_name', 'author__user__username', 'content'
    ]
    list_filter = ('approved', 'replied_on', 'updated_on')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        updated_count = queryset.update(approved=True)
        self.message_user(
            request, f'{updated_count} comments have been approved.'
            )
