from django.http import HttpResponseRedirect
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from reviews.models import Review, Comment
from reviews.admin import ReviewAdmin, CommentAdmin
from profiles.models import UserProfile
from .forms import CommentForm
from django.core.paginator import Paginator
from django.utils import timezone

User = get_user_model()


class ReviewListViewPaginationTest(TestCase):
    """
    Test to see if the reviews render correctly with pagination and the average rating.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.users = []

        # Create 10 test users with profiles
        for i in range(10):
            user = User.objects.create_user(
                first_name=f'User{i}',
                username=f'user_{i}',
                email=f'user_{i}@example.com',
                password='password'
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            self.users.append(profile)

        # Create 10 test reviews with authors set to user profiles
        for i in range(10):
            Review.objects.create(
                author=self.users[i],
                rating=(i % 5) + 1,
                content=f"Content of Test Review {i+1}",
                approved=True,
                created_on=timezone.now() - timezone.timedelta(days=i)
            )

    def test_pagination(self):
        """
        Test for pagination on reviews page.
        """
        url = reverse('reviews')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reviews = Review.objects.all().order_by('-created_on')
        results_per_page = 6
        paginator = Paginator(reviews, results_per_page)
        self.assertEqual(paginator.num_pages, 2)

    def test_average_rating(self):
        """
        Test for average review rating.
        """
        reviews = Review.objects.all()
        total_ratings = sum(review.rating for review in reviews)
        average_rating = total_ratings / len(reviews)
        expected_average_rating = 3
        self.assertAlmostEqual(average_rating, expected_average_rating, delta=0.01)


class ReviewDetailViewTest(TestCase):
    """
    Test to check the review details page for authenticated and non-authenticated users.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )

        self.testuser.save()
        
        self.review = Review.objects.create(
            author=UserProfile.objects.get_or_create(user=self.testuser)[0],
            rating=4,
            content="Test Review Content",
            approved=True
        )

        self.review_id = self.review.id

    def test_non_authenticated_user(self):
        """
        Non authenticated user view checks to ensure that forms are inaccessible and information
        is read-only.
        """
        url = reverse('review_detail', kwargs={'review_id': self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/review_detail.html') 
        self.assertNotContains(response, 'button type="submit"', html=True)
        self.assertNotContains(response, '<form id="commentForm" method="POST">')

    def test_authenticated_user(self):
        """
        Authenticated user view checks that comment form and like form is available.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse('review_detail', kwargs={'review_id': self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/review_detail.html')
        # Checking if comment form exists
        self.assertRegex(response.content.decode('utf-8'), r'<form\s+id="commentForm"\s+method="POST"')
        # Checking if like form exists
        self.assertRegex(response.content.decode('utf-8'), r'<button[^>]*type="submit"')


class EditCommentViewTest(TestCase):
    """
    Test case for editing a comment view.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )

        self.testuser.save()

        self.review = Review.objects.create(
            author=UserProfile.objects.get_or_create(user=self.testuser)[0],
            rating=4,
            content="Test Review Content",
            approved=True
        )

        self.comment = Comment.objects.create(
            author=UserProfile.objects.get_or_create(user=self.testuser)[0],
            review=self.review,
            content="Test comment"
        )

        self.review_id = self.review.id
        self.comment_id = self.comment.id

    def test_add_comment_valid_post_redirects(self):
        """
        POSTing valid comment data to review_detail redirects back to the review.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse('review_detail', kwargs={'review_id': self.review.id})
        response = self.client.post(url, data={'content': 'Test comment content'})
        self.assertEqual(response.status_code, 302)

    def test_edit_comment_non_authenticated_user(self):
        """
        Test that non-authenticated users cannot access the edit comment view.
        """
        url = reverse(
            'edit_comment',
            kwargs={'review_id': self.review_id, 'comment_id': self.comment_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_comment_valid_post(self):
        """
        Test editing a comment with valid data.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse(
            'edit_comment',
            kwargs={'review_id': self.review_id, 'comment_id': self.comment_id}
        )
        response = self.client.post(url, {'content': 'Updated comment'})
        self.assertRedirects(response, reverse('review_detail', args=[self.review_id]), fetch_redirect_response=False)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment')

    def test_edit_comment_invalid_post(self):
        """
        Test editing a comment with invalid (empty) data does not save and returns 200.
        """
        from reviews.views import edit_comment
        factory = RequestFactory()
        url = reverse('edit_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        request = factory.post(url, {'content': ''})
        request.user = self.testuser
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        response = edit_comment(request, review_id=self.review_id, comment_id=self.comment_id)
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Test comment')

    def test_edit_comment_wrong_user(self):
        """
        Test that a user cannot edit another user's comment.
        """
        User.objects.create_user(
            first_name='Other',
            username='otheruser',
            email='other@example.com',
            password='password'
        )
        self.client.login(username='otheruser', password='password')
        url = reverse('edit_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        response = self.client.post(url, {'content': 'Hijacked content'})
        self.assertRedirects(response, reverse('review_detail', args=[self.review_id]), fetch_redirect_response=False)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Test comment')


class AddCommentValidationTest(TestCase):
    """
    Test that submitting an invalid comment form returns errors in context.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.review = Review.objects.create(
            author=UserProfile.objects.get_or_create(user=self.testuser)[0],
            rating=4,
            content="Test Review Content",
            approved=True
        )

    def test_empty_comment_returns_form_with_errors(self):
        """
        POSTing an empty comment should not create a comment and the
        bound form should report validation errors on the content field.
        """
        from reviews.views import review_detail
        factory = RequestFactory()
        request = factory.post(
            reverse('review_detail', kwargs={'review_id': self.review.id}),
            data={'content': ''}
        )
        request.user = self.testuser
        # Attach session and message storage required by the view
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        comment_count_before = Comment.objects.count()
        response = review_detail(request, review_id=self.review.id)

        # Invalid submission must not redirect (302 means success path taken)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), comment_count_before)
        # The form itself must be invalid with content errors
        form = CommentForm(data={'content': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


class DeleteCommentViewTest(TestCase):
    """
    Test case for deleting a comment view.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )

        self.testuser.save()

        self.review = Review.objects.create(
            author=UserProfile.objects.get_or_create(user=self.testuser)[0],
            rating=4,
            content="Test Review Content",
            approved=True
        )

        self.comment = Comment.objects.create(
            author=UserProfile.objects.get_or_create(user=self.testuser)[0],
            review=self.review,
            content="Test comment"
        )

        self.review_id = self.review.id
        self.comment_id = self.comment.id

    def test_delete_comment_authenticated_user(self):
        """
        Test deleting a comment by an authenticated user.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse('delete_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=self.comment_id).exists())

    def test_delete_comment_non_authenticated_user(self):
        """
        Test that non-authenticated users cannot delete comments.
        """
        url = reverse(
            'delete_comment',
            kwargs={'review_id': self.review_id, 'comment_id': self.comment_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_delete_comment_from_profile_page_redirects_to_profile(self):
        """
        POSTing source_page=profile should redirect to the profile page, not the review detail.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse('delete_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        response = self.client.post(url, data={'source_page': 'profile'})
        self.assertRedirects(response, reverse('profile_page'), fetch_redirect_response=False)
        self.assertFalse(Comment.objects.filter(id=self.comment_id).exists())

    def test_delete_comment_without_source_page_redirects_to_review(self):
        """
        Without source_page=profile the redirect should go to the review detail page.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse('delete_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('review_detail', kwargs={'review_id': self.review_id}), fetch_redirect_response=False)
        self.assertFalse(Comment.objects.filter(id=self.comment_id).exists())

    def test_delete_comment_wrong_user(self):
        """
        Test that a user cannot delete another user's comment.
        """
        User.objects.create_user(
            first_name='Other', username='otheruser',
            email='other@example.com', password='password'
        )
        self.client.login(username='otheruser', password='password')
        url = reverse(
            'delete_comment',
            kwargs={'review_id': self.review_id, 'comment_id': self.comment_id}
        )
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse('review_detail', kwargs={'review_id': self.review_id}),
            fetch_redirect_response=False
        )
        self.assertTrue(Comment.objects.filter(id=self.comment_id).exists())


class CreateReviewViewTest(TestCase):
    """
    Test cases for creating a review.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )

        self.testuser.save()

    def test_authenticated_user_without_review(self):
        """
        Test the behavior of creating a review for an authenticated user without an existing review.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('create_review'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/review_form.html')

    def test_authenticated_user_with_existing_review(self):
        """
        Test the behavior of creating a review for an authenticated user with an existing review.
        """
        Review.objects.create(author=self.testuser.profile, rating=4, content="Test Review Content", approved=True)
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('create_review'))
        self.assertRedirects(response, reverse('profile_page'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_user(self):
        """
        Test the behavior of attempting to create a review for an authenticated user.
        """
        response = self.client.get(reverse('create_review'))
        self.assertRedirects(response, '/accounts/login/?next=/reviews/create-review/')
        self.assertEqual(response.status_code, 302)

    def test_valid_form_submission(self):
        """
        Test submitting a valid review form.
        """
        self.client.login(username='fakeuser', password='password')
        form_data = {'rating': 4, 'content': 'Valid review content'}
        response = self.client.post(reverse('create_review'), data=form_data)
        self.assertRedirects(response, reverse('profile_page'))
        self.assertEqual(response.status_code, 302)

    def test_invalid_form_submission(self):
        """
        Test submitting an invalid review form.
        """
        self.client.login(username='fakeuser', password='password')
        form_data = {'content': 'Invalid review content'}
        response = self.client.post(reverse('create_review'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/review_form.html')
        self.assertTrue('form' in response.context)


class UpdateReviewViewTest(TestCase):
    """
    Test cases for updating a review.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.testuser.save()

    def test_authenticated_user_with_existing_review(self):
        """
        Test the behavior of the update_review view for an authenticated user with an existing review.
        """
        review = Review.objects.create(author=self.testuser.profile, rating=4, content="Test Review Content", approved=True)
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('update_review', kwargs={'review_id': review.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/review_form.html')
    
    def test_authenticated_user_without_review(self):
        """
        Test the behavior of the update_review view for an authenticated user without an existing review.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('update_review', kwargs={'review_id': 123}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile_page'))

    def test_unauthenticated_user(self):
        """
        Test the behavior of the update_review view for an unauthenticated user.
        """
        response = self.client.get(reverse('update_review', kwargs={'review_id': 123}))
        self.assertRedirects(response, '/accounts/login/?next=/reviews/update-review/123/')
        self.assertEqual(response.status_code, 302)

    def test_valid_form_submission(self):
        """
        Test submitting a valid update review form.
        """
        review = Review.objects.create(
            author=self.testuser.profile, rating=3,
            content='Original content', approved=True
        )
        self.client.login(username='fakeuser', password='password')
        form_data = {'rating': 4, 'content': 'Updated review content'}
        response = self.client.post(
            reverse('update_review', kwargs={'review_id': review.id}),
            data=form_data
        )
        self.assertRedirects(response, reverse('profile_page'))
        review.refresh_from_db()
        self.assertEqual(review.content, 'Updated review content')

    def test_invalid_form_submission(self):
        """
        Test submitting an invalid update review form.
        """
        review = Review.objects.create(
            author=self.testuser.profile, rating=3,
            content='Original content', approved=True
        )
        self.client.login(username='fakeuser', password='password')
        form_data = {'content': 'Missing rating'}
        response = self.client.post(
            reverse('update_review', kwargs={'review_id': review.id}),
            data=form_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/review_form.html')
        self.assertTrue('form' in response.context)


class DeleteReviewViewTest(TestCase):
    """
    Test cases for deleting a review.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.testuser.save()

        # Creating a test review
        self.review = Review.objects.create(
            author=self.testuser.profile,
            rating=4,
            content="Test Review Content",
            approved=True
        )

    def test_authenticated_user_delete_review(self):
        """
        Test deleting a review by an authenticated user.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.post(reverse('delete_review', kwargs={'review_id': self.review.id}))
        self.assertRedirects(response, reverse('profile_page'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_unauthenticated_user_delete_review(self):
        """
        Test attempting to delete a review by an unauthenticated user.
        """
        response = self.client.post(reverse('delete_review', kwargs={'review_id': self.review.id}))
        self.assertRedirects(
            response,
            f'/accounts/login/?next=/reviews/delete-review/{self.review.id}/'
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_not_owned(self):
        """
        Test that a user cannot delete another user's review.
        """
        User.objects.create_user(
            first_name='Other', username='otheruser',
            email='other@example.com', password='password'
        )
        self.client.login(username='otheruser', password='password')
        response = self.client.post(
            reverse('delete_review', kwargs={'review_id': self.review.id})
        )
        self.assertRedirects(response, reverse('profile_page'))
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_get_request(self):
        """
        Test that a GET to delete_review redirects without deleting.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(
            reverse('delete_review', kwargs={'review_id': self.review.id})
        )
        self.assertRedirects(response, reverse('profile_page'))
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())


class LikeToggleViewTest(TestCase):
    """
    Test cases for toggling the like status for a review.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.user_profile = UserProfile.objects.get_or_create(user=self.testuser)[0]

        self.review = Review.objects.create(
            author=self.user_profile,
            rating=4,
            content="Test Review Content",
            approved=True
        )
        
    def test_like_toggle(self):
        """
        Test toggling the like status for a review.
        """
        self.client.login(username='fakeuser', password='password')
        review_id = self.review.id
        response = self.client.post(reverse('like_review', args=[review_id]))
        self.assertIsInstance(response, HttpResponseRedirect)
        updated_review = Review.objects.get(id=review_id)
        self.assertTrue(updated_review.likes.filter(id=self.user_profile.id).exists())
        response = self.client.post(reverse('like_review', args=[review_id]))
        self.assertIsInstance(response, HttpResponseRedirect)
        updated_review = Review.objects.get(id=review_id)
        self.assertFalse(updated_review.likes.filter(id=self.user_profile.id).exists())

    def test_like_toggle_uses_url_review_id_not_post_body(self):
        """
        View must use the URL's review_id, not any like_id submitted in the POST body.
        A mismatched like_id in POST data must not affect a different review.
        """
        other_user = User.objects.create_user(
            username='otheruser', email='other@fakemail.com', password='password'
        )
        other_profile = UserProfile.objects.get_or_create(user=other_user)[0]
        other_review = Review.objects.create(
            author=other_profile,
            rating=3,
            content="Other Review",
            approved=True
        )
        self.client.login(username='fakeuser', password='password')
        # POST to self.review's URL but include other_review's id as like_id
        self.client.post(
            reverse('like_review', args=[self.review.id]),
            data={'like_id': other_review.id}
        )
        # self.review should be liked (URL governs)
        self.assertTrue(self.review.likes.filter(id=self.user_profile.id).exists())
        # other_review must be untouched
        self.assertFalse(other_review.likes.filter(id=self.user_profile.id).exists())


class ReviewModelTest(TestCase):
    """
    Test the string representation of Review and Comment models.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.profile = UserProfile.objects.get_or_create(user=self.testuser)[0]
        self.review = Review.objects.create(
            author=self.profile,
            rating=4,
            content='Test Review Content',
            approved=True
        )
        self.comment = Comment.objects.create(
            author=self.profile,
            review=self.review,
            content='Test comment'
        )

    def test_review_str(self):
        """Test Review __str__ representation."""
        self.assertIn('Written by', str(self.review))

    def test_comment_str(self):
        """Test Comment __str__ representation."""
        self.assertIn('Written by', str(self.comment))


class ReviewAdminTest(TestCase):
    """
    Test admin actions for Review and Comment.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            first_name='Admin',
            username='adminuser',
            email='admin@test.com',
            password='adminpass'
        )
        self.profile = UserProfile.objects.get_or_create(user=self.admin_user)[0]
        self.review = Review.objects.create(
            author=self.profile,
            rating=4,
            content='Test Review Content',
            approved=False
        )
        self.comment = Comment.objects.create(
            author=self.profile,
            review=self.review,
            content='Test comment',
            approved=False
        )

    def _get_request(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        return request

    def test_approve_reviews(self):
        """Test approve_reviews admin action."""
        admin = ReviewAdmin(Review, AdminSite())
        admin.approve_reviews(
            self._get_request(), Review.objects.filter(id=self.review.id)
        )
        self.review.refresh_from_db()
        self.assertTrue(self.review.approved)

    def test_approve_comments(self):
        """Test approve_comments admin action."""
        admin = CommentAdmin(Comment, AdminSite())
        admin.approve_comments(
            self._get_request(), Comment.objects.filter(id=self.comment.id)
        )
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.approved)



class ModerationAndPermissionTest(TestCase):
    """
    Regression tests for review/comment moderation and permissions:
    pending reviews stay private, edits are re-moderated, comments need a
    login and an approved review, and likes only change via POST.
    """
    def setUp(self):
        self.author = User.objects.create_user(
            username='author', email='author@example.com',
            password='password', first_name='Author'
        )
        self.other = User.objects.create_user(
            username='other', email='other@example.com',
            password='password', first_name='Other'
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@example.com',
            password='password', is_staff=True
        )
        self.pending = Review.objects.create(
            author=self.author.profile, rating=2,
            content='Pending review text', approved=False
        )
        self.approved = Review.objects.create(
            author=self.other.profile, rating=5,
            content='Approved review text', approved=True
        )

    def detail_url(self, review):
        return reverse('review_detail', args=[review.id])

    # Pending reviews are private
    def test_pending_review_hidden_from_anonymous_and_other_users(self):
        self.assertEqual(self.client.get(self.detail_url(self.pending)).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.detail_url(self.pending)).status_code, 404)

    def test_pending_review_visible_to_author_and_staff(self):
        for user in (self.author, self.staff):
            self.client.force_login(user)
            response = self.client.get(self.detail_url(self.pending))
            self.assertContains(response, 'Pending review text')
            self.assertContains(response, 'pending admin approval')
            self.assertNotContains(response, 'id="commentForm"')

    # Comments
    def test_anonymous_comment_post_redirects_to_login(self):
        response = self.client.post(
            self.detail_url(self.approved), {'content': 'Drive-by comment'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('account_login'), response['Location'])
        self.assertFalse(Comment.objects.exists())

    def test_cannot_comment_on_pending_review(self):
        self.client.force_login(self.author)
        self.client.post(self.detail_url(self.pending), {'content': 'Early comment'})
        self.assertFalse(Comment.objects.exists())

    def test_new_comment_is_published_immediately(self):
        self.client.force_login(self.author)
        self.client.post(self.detail_url(self.approved), {'content': 'Straight in'})
        comment = Comment.objects.get()
        self.assertTrue(comment.approved)
        self.client.logout()
        self.assertContains(self.client.get(self.detail_url(self.approved)), 'Straight in')

    def test_editing_comment_keeps_it_published(self):
        comment = Comment.objects.create(
            review=self.approved, author=self.author.profile, content='Original'
        )
        self.client.force_login(self.author)
        self.client.post(
            reverse('edit_comment', args=[self.approved.id, comment.id]),
            {'content': 'Changed later'}
        )
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Changed later')
        self.assertTrue(comment.approved)

    def test_comment_hidden_by_staff_stays_hidden_after_edit(self):
        comment = Comment.objects.create(
            review=self.approved, author=self.author.profile,
            content='Spam', approved=False
        )
        self.client.force_login(self.author)
        self.client.post(
            reverse('edit_comment', args=[self.approved.id, comment.id]),
            {'content': 'Still spam'}
        )
        comment.refresh_from_db()
        self.assertFalse(comment.approved)

    def test_comment_form_has_clear_button(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url(self.approved))
        self.assertContains(
            response, '<button type="reset" class="red-button">Clear</button>', html=True
        )

    def test_comment_cannot_be_moved_to_another_review(self):
        own_review = Review.objects.create(
            author=self.staff.profile, rating=4, content='x', approved=True
        )
        comment = Comment.objects.create(
            review=self.approved, author=self.author.profile, content='Mine'
        )
        self.client.force_login(self.author)
        response = self.client.post(
            reverse('edit_comment', args=[own_review.id, comment.id]),
            {'content': 'Moved?'}
        )
        self.assertEqual(response.status_code, 404)
        comment.refresh_from_db()
        self.assertEqual(comment.review_id, self.approved.id)
        self.assertEqual(comment.content, 'Mine')

    # Reviews
    def test_editing_approved_review_requires_reapproval(self):
        self.client.force_login(self.other)
        self.client.post(
            reverse('update_review', args=[self.approved.id]),
            {'rating': 1, 'content': 'Changed after approval'}
        )
        self.approved.refresh_from_db()
        self.assertEqual(self.approved.content, 'Changed after approval')
        self.assertFalse(self.approved.approved)
        self.assertIsNotNone(self.approved.updated_on)

    def test_saving_review_unchanged_keeps_approval(self):
        self.client.force_login(self.other)
        self.client.post(
            reverse('update_review', args=[self.approved.id]),
            {'rating': 5, 'content': 'Approved review text'}
        )
        self.approved.refresh_from_db()
        self.assertTrue(self.approved.approved)
        self.assertIsNone(self.approved.updated_on)

    # Likes
    def test_like_via_get_is_rejected(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('like_review', args=[self.approved.id]))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.approved.likes.exists())

    def test_cannot_like_pending_review(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse('like_review', args=[self.pending.id]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.pending.likes.exists())



class AdminSearchTest(TestCase):
    """
    Searching reviews and comments in the admin must work (it used to
    raise a 500 because 'author' is a relation, not a text field).
    """
    def setUp(self):
        self.staff = User.objects.create_superuser(
            'boss', 'boss@example.com', 'password'
        )
        author = User.objects.create_user(
            'searchable', 'searchable@example.com', 'password',
            first_name='Searchable'
        )
        review = Review.objects.create(
            author=author.profile, rating=5, content='Great lessons'
        )
        Comment.objects.create(
            review=review, author=author.profile, content='Agreed'
        )
        self.client.force_login(self.staff)

    def test_review_search_by_author_name(self):
        response = self.client.get('/admin/reviews/review/?q=Searchable')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cl'].result_count, 1)

    def test_comment_search_by_author_name(self):
        response = self.client.get('/admin/reviews/comment/?q=Searchable')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cl'].result_count, 1)



class QueryCountStabilityTest(TestCase):
    """
    Page cost must not grow with content (no N+1 queries): each page makes
    the same number of database queries with 1 item as with 5.
    """
    def setUp(self):
        self.viewer = User.objects.create_user(
            'viewer', 'viewer@example.com', 'password', first_name='Viewer')
        self.target = User.objects.create_user(
            'target', 'target@example.com', 'password', first_name='Target')
        self.target_review = Review.objects.create(
            author=self.target.profile, rating=5, content='t', approved=True)
        self.added = 0

    def add_items(self, count):
        """Each item: another user's approved review that the viewer
        commented on, plus a comment by that user on the target review."""
        for _ in range(count):
            self.added += 1
            user = User.objects.create_user(
                f'u{self.added}', f'u{self.added}@example.com', 'password',
                first_name=f'User{self.added}')
            review = Review.objects.create(
                author=user.profile, rating=4, content='x', approved=True)
            Comment.objects.create(
                review=review, author=self.viewer.profile,
                content='c', approved=True)
            Comment.objects.create(
                review=self.target_review, author=user.profile,
                content='c', approved=True)
        UserProfile.objects.update(approved=True)

    def query_count(self, url, user=None):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        if user:
            self.client.force_login(user)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.client.logout()
        self.assertEqual(response.status_code, 200)
        return len(queries)

    def assert_flat(self, url, user=None):
        self.add_items(1)
        with_one = self.query_count(url, user)
        self.add_items(4)
        with_five = self.query_count(url, user)
        self.assertEqual(with_one, with_five, f'{url}: queries grow with content')

    def test_reviews_list(self):
        self.assert_flat(reverse('reviews'))

    def test_review_detail(self):
        self.assert_flat(reverse('review_detail', args=[self.target_review.id]))

    def test_profile_page(self):
        self.assert_flat(reverse('profile_page'), self.viewer)

    def test_user_profiles(self):
        self.assert_flat(reverse('user_profiles'))
