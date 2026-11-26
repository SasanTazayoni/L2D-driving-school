from . import views
from django.urls import path

urlpatterns = [
    path("", views.ReviewList.as_view(), name="reviews"),
    path("<int:review_id>/", views.review_detail, name="review_detail"),
    path("create-review/", views.create_review, name="create_review"),
    path('update-review/<int:review_id>/',
         views.update_review, name='update_review'),
    path('delete-review/<int:review_id>/',
         views.delete_review, name='delete_review'),
    path('<int:review_id>/edit-comment/<int:comment_id>/',
         views.edit_comment, name='edit_comment'),
    path('<int:review_id>/delete-comment/<int:comment_id>/',
         views.delete_comment, name='delete_comment'),
    path("like/<int:review_id>/", views.like_toggle, name="like_review"),
]
