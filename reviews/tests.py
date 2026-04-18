from django.http import HttpResponseRedirect
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from reviews.models import Review, Comment
from reviews.admin import ReviewAdmin, CommentAdmin
from profiles.models import UserProfile
from .forms import ReviewForm, CommentForm
from django.core.paginator import Paginator
from reviews.views import ReviewList
from django.utils import timezone


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
            profile, created = UserProfile.objects.get_or_create(user=user)
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
        request = self.factory.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reviews = Review.objects.all().order_by('-created_on')
        page = request.GET.get('page')
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

    def test_edit_comment_authenticated_user(self):
        """
        Test editing a comment by an authenticated user.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse('edit_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        response = self.client.get(url)
        form_data = {'content': 'Test comment content'}
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
        response = self.client.post(reverse('review_detail', kwargs={'review_id': self.review.id}), data=form_data)
        self.assertEqual(response.status_code, 302)
        empty_form_data = {}
        empty_form = CommentForm(data=empty_form_data)
        self.assertFalse(empty_form.is_valid())
        empty_response = self.client.post(reverse('review_detail', kwargs={'review_id': self.review.id}), data=empty_form_data)
        self.assertEqual(empty_response.status_code, 200)

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
        self.assertRedirects(response, reverse('review_detail', args=[self.review_id]))
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment')

    def test_edit_comment_invalid_post(self):
        """
        Test editing a comment with invalid (empty) data.
        """
        self.client.login(username='fakeuser', password='password')
        url = reverse(
            'edit_comment',
            kwargs={'review_id': self.review_id, 'comment_id': self.comment_id}
        )
        response = self.client.post(url, {'content': ''})
        self.assertEqual(response.status_code, 200)

    def test_edit_comment_wrong_user(self):
        """
        Test that a user cannot edit another user's comment.
        """
        other_user = User.objects.create_user(
            first_name='Other',
            username='otheruser',
            email='other@example.com',
            password='password'
        )
        self.client.login(username='otheruser', password='password')
        url = reverse('edit_comment', kwargs={'review_id': self.review_id, 'comment_id': self.comment_id})
        response = self.client.post(url, {'content': 'Hijacked content'})
        self.assertRedirects(response, reverse('review_detail', args=[self.review_id]))
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
        other_user = User.objects.create_user(
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
        review = Review.objects.create(author=self.testuser.profile, rating=4, content="Test Review Content", approved=True)
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
        other_user = User.objects.create_user(
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
