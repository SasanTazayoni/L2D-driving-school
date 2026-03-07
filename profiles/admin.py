from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from django_summernote.admin import SummernoteModelAdmin

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
    """
    Custom admin panel for User model to adjust list display.
    """
    list_display = ('username', 'email', 'get_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def get_name(self, obj):
        return obj.first_name
    get_name.short_description = 'Name'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(SummernoteModelAdmin):
    """
    Custom admin panel for managing user profiles.
    """
    list_display = ('get_name', 'created_on', 'approved')
    search_fields = ['user__first_name', 'about_me']
    summernote_fields = ('about_me',)
    actions = ['approve_profiles']

    def get_name(self, obj):
        return obj.user.first_name
    get_name.short_description = 'Name'

    def approve_profiles(self, request, queryset):
        updated_count = queryset.update(approved=True)
        self.message_user(
            request, f'{updated_count} profiles have been approved.'
        )
