from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField


class UserProfileQuerySet(models.QuerySet):
    def public(self):
        """Profiles anyone may see: approved, and not staff accounts."""
        return self.filter(approved=True, user__is_staff=False)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        blank=False,
        null=False
    )
    profile_picture = CloudinaryField('image', null=True, blank=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    about_me = models.TextField(max_length=400, blank=True, null=True)
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = UserProfileQuerySet.as_manager()

    @property
    def is_public(self):
        """Whether anyone (including logged-out visitors) may see it."""
        return self.approved and not self.user.is_staff

    def __str__(self):
        # Accounts made with createsuperuser have no first name.
        return self.user.first_name or self.user.username
