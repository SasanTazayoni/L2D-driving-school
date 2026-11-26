from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from .models import Review, Comment
from .forms import ReviewForm, CommentForm
from django.contrib.auth.decorators import login_required


def get_visible_review(request, review_id):
    """
    Return the review if the current user is allowed to see it.

    Approved reviews are public. Reviews awaiting approval are only visible
    to their author and to staff; everyone else gets a 404, so pending
    content cannot be read by guessing review IDs.
    """
    review = get_object_or_404(
        Review.objects.select_related('author'), id=review_id
    )
    user = request.user
    is_author = (
        user.is_authenticated and review.author.user_id == user.id
    )
    if review.approved or is_author or user.is_staff:
        return review
    raise Http404("No Review matches the given query.")


class ReviewList(generic.ListView):
    """
    Render a paginated list of reviews (6 per page) with an average rating.
    """
    queryset = (
        Review.objects
        .filter(approved=True)
        .order_by("-created_on")
        .select_related('author')
    )
    queryset = queryset.annotate(
        comment_count=Count('comments',
                            filter=Q(comments__approved=True),
                            distinct=True)
    )
    queryset = queryset.annotate(like_count=Count('likes', distinct=True))
    template_name = "reviews/reviews.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        average_rating = (
            Review.objects
            .filter(approved=True)
            .aggregate(avg_rating=Avg('rating'))['avg_rating']
        )
        context['average_rating'] = (
            round(average_rating, 2) if average_rating else None
        )
        return context


def review_detail(request, review_id):
    """
    Display the details of an individual review provided by a user.
    """

    review = get_visible_review(request, review_id)
    comments = review.comments.all().order_by("-replied_on")
    comment_count = review.comments.filter(approved=True).count()
    like_count = review.likes.count()
    liked = False

    if request.user.is_authenticated:
        liked = review.likes.filter(user=request.user).exists()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not review.approved:
            messages.error(
                request, 'Comments open once this review has been approved.'
            )
            return redirect('review_detail', review_id=review_id)
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user.profile
            comment.review = review
            comment.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Your comment was submitted and is now pending admin approval.'
            )
            return redirect('review_detail', review_id=review_id)
    else:
        comment_form = CommentForm()

    context = {
        'review': review,
        "comments": comments,
        "comment_count": comment_count,
        "like_count": like_count,
        "liked": liked,
        "review_id": review_id,
        "comment_form": comment_form,
    }

    return render(request, "reviews/review_detail.html", context)


@login_required
def edit_comment(request, review_id, comment_id):
    """
    Edit a comment authored by the current user on a review.
    """
    review = get_visible_review(request, review_id)
    # The comment must belong to the review in the URL, so a comment can
    # never be moved onto a different review.
    comment = get_object_or_404(Comment, id=comment_id, review=review)

    if comment.author.user != request.user:
        messages.error(request, 'You are not authorised to edit this comment.')
        return HttpResponseRedirect(reverse('review_detail', args=[review_id]))

    if request.method == "POST":
        comment_form = CommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            if comment_form.has_changed():
                edited_comment = comment_form.save(commit=False)
                # Changed text must be moderated again before it is public.
                edited_comment.approved = False
                edited_comment.save()
                messages.success(
                    request,
                    'Comment updated. It is now pending admin approval.'
                )
            else:
                messages.info(request, 'No changes were made.')
            return HttpResponseRedirect(
                reverse('review_detail', args=[review_id])
            )
        else:
            messages.error(request, 'Error updating comment.')
    else:
        comment_form = CommentForm(instance=comment)

    comment_count = review.comments.filter(approved=True).count()
    like_count = review.likes.count()
    is_edit_comment_view = True

    context = {
        'review_id': review_id,
        'review': review,
        'comment_form': comment_form,
        'is_edit_comment_view': is_edit_comment_view,
        'comment_count': comment_count,
        'like_count': like_count,
    }

    return render(request, 'reviews/review_detail.html', context)


@login_required
def delete_comment(request, review_id, comment_id):
    """
    Delete a comment authored by the current user on a review.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    review_id = comment.review.id

    if comment.author.user != request.user:
        messages.error(
            request,
            'You are not authorised to delete this comment.'
        )
        return redirect('review_detail', review_id=review_id)

    if request.method == "POST":
        comment.delete()
        messages.success(request, 'Comment removed.')
        if request.POST.get('source_page') == 'profile':
            return redirect('profile_page')

    return redirect(reverse('review_detail', args=[review_id]))


@login_required
def create_review(request):
    """
    Create a review authored by the current user.
    """
    profile = request.user.profile
    existing_review = Review.objects.filter(author=profile).first()

    if existing_review:
        messages.info(request, 'You have already made a review.')
        return redirect('profile_page')

    form = ReviewForm()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.author = profile
            review.save()
            messages.success(
                request,
                'Your review was submitted and is now pending admin approval.'
            )
            return redirect('profile_page')

    context = {'form': form}
    return render(request, "reviews/review_form.html", context)


@login_required
def update_review(request, review_id):
    """
    Update a review authored by the current user.
    """
    profile = request.user.profile
    existing_review = (
        Review.objects
        .filter(author=profile, id=review_id)
        .first()
    )

    if not existing_review:
        messages.info(request, 'You must create a review before editing.')
        return redirect('profile_page')

    form = ReviewForm(instance=existing_review)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            if form.has_changed():
                review = form.save(commit=False)
                review.updated_on = timezone.now()
                # Changed text must be moderated again before it is public.
                review.approved = False
                review.save()
                messages.success(
                    request,
                    'Your review has been updated and is now pending '
                    'admin approval.'
                )
            else:
                messages.info(request, 'No changes were made to your review.')
            return redirect('profile_page')

    context = {'form': form}
    return render(request, "reviews/review_form.html", context)


@login_required
def delete_review(request, review_id):
    """
    Delete a review authored by the current user.
    """
    profile = request.user.profile
    existing_review = (
        Review.objects
        .filter(author=profile, id=review_id)
        .first()
    )

    if not existing_review:
        messages.info(request, 'There is no review to delete.')
        return redirect('profile_page')

    if request.method == 'POST':
        existing_review.delete()
        messages.success(request, 'Your review has been deleted.')
        return redirect('profile_page')

    return redirect('profile_page')


@login_required
@require_POST
def like_toggle(request, review_id):
    """
    Toggles the like status for an approved review. POST only, so a link
    or image on another site cannot like or unlike on a user's behalf.
    """
    review = get_object_or_404(Review, id=review_id, approved=True)
    user_profile = request.user.profile

    if review.likes.filter(id=user_profile.id).exists():
        review.likes.remove(user_profile)
    else:
        review.likes.add(user_profile)

    return HttpResponseRedirect(reverse('review_detail', args=[review_id]))
