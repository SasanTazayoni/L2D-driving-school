from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.contrib import messages
from profiles.models import UserProfile
from reviews.models import Review, Comment


def home(request):
    """
    Renders the home page.
    """
    return render(request, 'core/index.html')


@login_required(login_url='/accounts/login/')
def appointments(request):
    """
    Renders the appointments page if the user is authenticated,
    otherwise redirects to the login page.

    User profiles must also be approved by the admin to access this page.
    """
    if request.user.profile.approved:
        return render(request, 'core/appointments.html')
    else:
        messages.error(
            request,
            (
                "You are not currently authorised to book appointments. "
                "Please contact your driving instructor."
            )
        )
        return redirect(reverse('contact'))


def contact(request):
    """
    Renders the contact page.
    """
    return render(request, 'core/contact.html')


def user_profiles(request):
    """
    Renders the user profiles page which consists of a paginated gallery of all
    users.
    """
    search_query = ''

    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')

    user_profiles = (
        UserProfile.objects
        .filter(user__first_name__icontains=search_query)
        .order_by('user__first_name')
    )

    page = request.GET.get('page')
    profiles_per_page = 12
    paginator = Paginator(user_profiles, profiles_per_page)

    try:
        user_profiles = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        user_profiles = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        user_profiles = paginator.page(page)

    context = {
        'user_profiles': user_profiles,
        'search_query': search_query,
        'paginator': paginator,
    }
    return render(request, 'core/user_profiles.html', context)


def profile_detail(request, user_id):
    """
    Renders the profile page for a particular user.
    """
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    comment_count = (
        Comment.objects
        .filter(review__author=user_profile, approved=True).count()
    )
    like_count = (
        Review.objects
        .filter(author=user_profile)
        .aggregate(total_likes=Count('likes'))['total_likes'] or 0
    )

    context = {
        'user_profile': user_profile,
        'comment_count': comment_count,
        'like_count': like_count,
    }

    return render(request, 'core/profile_detail.html', context)
