from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
# Django passes `sender` to every receiver, even when it is not used.
def create_user_profile(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    if created:
        UserProfile.objects.create(
            user=instance,
        )
