from django.db import models
from profiles.models import UserProfile

RATING_CHOICES = (
    (1, "1 star"),
    (2, "2 stars"),
    (3, "3 stars"),
    (4, "4 stars"),
    (5, "5 stars")
)


class Review(models.Model):
    author = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="review",
        null=False,
        blank=False
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        null=False,
        blank=False
    )
    content = models.TextField(max_length=800, null=False, blank=False)
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    likes = models.ManyToManyField(
        UserProfile,
        related_name="user_reviews",
        blank=True
    )

    class Meta:
        ordering = ["-created_on"]
        indexes = [
            # Public review list: WHERE approved ORDER BY created_on DESC
            models.Index(
                fields=["approved", "-created_on"],
                name="review_approved_created_idx",
            ),
        ]

    def __str__(self):
        return f"Written by {self.author} on {self.created_on}"


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="commenter",
        null=False,
        blank=False
    )
    content = models.TextField(max_length=800, null=False, blank=False)
    approved = models.BooleanField(default=False)
    replied_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-replied_on"]
        indexes = [
            # Comment counts: WHERE review_id = ? AND approved
            models.Index(
                fields=["review", "approved"],
                name="comment_review_approved_idx",
            ),
        ]

    def __str__(self):
        return f"Written by {self.author} on {self.replied_on}"
