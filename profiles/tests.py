from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test.client import Client
from profiles.admin import CustomUserAdmin, UserProfileAdmin
from profiles.forms import CustomSignupForm
from profiles.models import UserProfile

User = get_user_model()


class ProfilePageViewTest(TestCase):
    """
    Test cases for the profile_page view.
    """
    def setUp(self):
        self.client = Client()
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )

    def test_authenticated_user_profile_page(self):
        """
        Test the profile page for an authenticated user.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/profile.html')
        self.assertEqual(response.context['profile'], self.testuser.profile)

    def test_unauthenticated_user_profile_page(self):
        """
        Test that an unauthenticated user is redirected to the login page.
        """
        response = self.client.get(reverse('profile_page'))
        self.assertRedirects(response, '/accounts/login/?next=/profile/')
        self.assertEqual(response.status_code, 302)


class EditProfileViewTest(TestCase):
    """
    Test cases for editing user profile.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.testuser.save()

    def test_authenticated_user_edit_profile(self):
        """
        Test editing profile for an authenticated user.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/edit_profile.html')

        self._test_form_submission()

    def test_unauthenticated_user_edit_profile(self):
        """
        Test accessing edit profile page for an unauthenticated user.
        """
        response = self.client.get(reverse('edit_profile'))
        self.assertRedirects(response, '/accounts/login/?next=/profile/edit/')
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_remove_picture(self):
        """
        Test editing profile with remove_picture flag clears the picture.
        """
        self.client.login(username='fakeuser', password='password')
        form_data = {
            'first_name': 'Fake',
            'email': 'fakeuser@fakemail.com',
            'remove_picture': 'on',
        }
        response = self.client.post(reverse('edit_profile'), form_data)
        self.assertRedirects(response, reverse('profile_page'))

    def _test_form_submission(self):
        """
        Test valid and invalid form submission.
        """
        # Invalid: empty form re-renders the page
        response = self.client.post(reverse('edit_profile'), {})
        self.assertEqual(response.status_code, 200)

        # Valid: filled form redirects to profile page
        form_data = {
            'first_name': 'Updated',
            'email': 'fakeuser@fakemail.com',
        }
        response = self.client.post(reverse('edit_profile'), form_data)
        self.assertRedirects(response, reverse('profile_page'))
        self.testuser.refresh_from_db()
        self.assertEqual(self.testuser.first_name, 'Updated')


class DeleteProfileViewTest(TestCase):
    """
    Test cases for deleting user profile.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        self.testuser.save()

    def test_authenticated_user_delete_profile(self):
        """
        Test deleting profile for an authenticated user.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.post(reverse('delete_profile'))
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(User.objects.count(), 0)

    def test_get_delete_profile_redirects(self):
        """
        Test that GET to delete_profile redirects to profile page.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('delete_profile'))
        self.assertRedirects(response, reverse('profile_page'))

    def test_unauthenticated_user_delete_profile(self):
        """
        Test accessing delete profile view for an unauthenticated user.
        """
        response = self.client.post(reverse('delete_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/profile/delete/')


class CustomSignupFormTest(TestCase):
    """
    Test cases for CustomSignupForm validation.
    """
    def setUp(self):
        User.objects.create_user(
            first_name='Existing',
            username='existinguser',
            email='existing@example.com',
            password='password'
        )

    def test_duplicate_email_raises_error(self):
        """Test that a duplicate email is rejected."""
        form = CustomSignupForm(data={
            'first_name': 'Test',
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_username_raises_error(self):
        """Test that a duplicate username is rejected."""
        form = CustomSignupForm(data={
            'first_name': 'Test',
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def signup_data(self, **overrides):
        data = {
            'first_name': 'Test',
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        data.update(overrides)
        return data

    def test_valid_signup(self):
        """A complete, unique signup is valid."""
        self.assertTrue(CustomSignupForm(data=self.signup_data()).is_valid())

    def test_missing_first_name_rejected(self):
        """The name field is required."""
        form = CustomSignupForm(data=self.signup_data(first_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_missing_email_rejected(self):
        """An email address is required."""
        form = CustomSignupForm(data=self.signup_data(email=''))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email_different_case_rejected(self):
        """Email uniqueness ignores case."""
        form = CustomSignupForm(
            data=self.signup_data(email='EXISTING@Example.com')
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_username_different_case_rejected(self):
        """Username uniqueness ignores case."""
        form = CustomSignupForm(data=self.signup_data(username='ExistingUser'))
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class ProfileAdminTest(TestCase):
    """
    Test admin actions and methods for UserProfile and User.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            first_name='Admin',
            username='adminuser',
            email='admin@test.com',
            password='adminpass'
        )

    def _get_request(self):
        request = self.factory.get('/')
        request.user = self.admin_user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        return request

    def test_custom_user_admin_get_name(self):
        """Test get_name in CustomUserAdmin returns first_name."""
        admin = CustomUserAdmin(User, AdminSite())
        self.assertEqual(admin.get_name(self.admin_user), 'Admin')

    def test_custom_user_admin_get_queryset(self):
        """Test get_queryset in CustomUserAdmin returns users."""
        admin = CustomUserAdmin(User, AdminSite())
        qs = admin.get_queryset(self._get_request())
        self.assertIn(self.admin_user, qs)

    def test_user_profile_admin_get_name(self):
        """Test get_name in UserProfileAdmin returns first_name."""
        admin = UserProfileAdmin(UserProfile, AdminSite())
        profile = UserProfile.objects.get(user=self.admin_user)
        self.assertEqual(admin.get_name(profile), 'Admin')

    def test_approve_profiles(self):
        """Test approve_profiles admin action sets approved=True."""
        admin = UserProfileAdmin(UserProfile, AdminSite())
        profile = UserProfile.objects.get(user=self.admin_user)
        profile.approved = False
        profile.save()
        admin.approve_profiles(
            self._get_request(),
            UserProfile.objects.filter(id=profile.id)
        )
        profile.refresh_from_db()
        self.assertTrue(profile.approved)


class ProfilePictureNullGuardTest(TestCase):
    """
    Ensure profile and profile_detail pages load without error for users
    who have no profile picture set (guards against AttributeError on .url).
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Nopic',
            username='nopicuser',
            email='nopic@example.com',
            password='password'
        )
        self.profile = UserProfile.objects.get_or_create(user=self.testuser)[0]
        self.profile.profile_picture = None
        self.profile.approved = True
        self.profile.save()

    def test_profile_page_without_picture(self):
        """Profile page returns 200 when the user has no profile picture."""
        self.client.login(username='nopicuser', password='password')
        response = self.client.get(reverse('profile_page'))
        self.assertEqual(response.status_code, 200)

    def test_profile_detail_without_picture(self):
        """Public profile detail page returns 200 when the user has no profile picture."""
        response = self.client.get(
            reverse('profile_detail', kwargs={'user_id': self.testuser.id})
        )
        self.assertEqual(response.status_code, 200)



class EditProfileSecurityTest(TestCase):
    """
    The email shown on the edit profile form is read-only on the server,
    not just in the browser, and the picture field renders correctly.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            'bob', 'bob@example.com', 'password', first_name='Bob')
        User.objects.create_user('alice', 'alice@example.com', 'password')
        self.client.force_login(self.user)

    def test_posted_email_is_ignored(self):
        response = self.client.post(reverse('edit_profile'), {
            'first_name': 'Robert', 'email': 'alice@example.com'})
        self.assertRedirects(response, reverse('profile_page'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Robert')
        self.assertEqual(self.user.email, 'bob@example.com')
        self.assertEqual(
            User.objects.filter(email='alice@example.com').count(), 1)

    def test_form_shows_current_email_as_disabled(self):
        html = self.client.get(reverse('edit_profile')).content.decode()
        self.assertIn('value="bob@example.com"', html)
        self.assertRegex(html, r'<input[^>]*name="email"[^>]*disabled')

    def test_picture_field_and_preview_with_existing_picture(self):
        profile = self.user.profile
        profile.profile_picture = 'sample_public_id'
        profile.save()
        html = self.client.get(reverse('edit_profile')).content.decode()
        self.assertIn('type="file" name="profile_picture"', html)
        self.assertIn('class="current-profile-picture"', html)
        self.assertIn('name="remove_picture"', html)
        self.assertNotIn('editProfile.js', html)

    def test_no_preview_or_remove_option_without_picture(self):
        html = self.client.get(reverse('edit_profile')).content.decode()
        self.assertIn('type="file" name="profile_picture"', html)
        self.assertNotIn('current-profile-picture', html)
        self.assertNotIn('name="remove_picture"', html)

    def test_saving_without_new_file_keeps_picture(self):
        profile = self.user.profile
        profile.profile_picture = 'sample_public_id'
        profile.save()
        self.client.post(reverse('edit_profile'), {'first_name': 'Bob'})
        profile.refresh_from_db()
        self.assertEqual(str(profile.profile_picture), 'sample_public_id')


class UserProfileStrTest(TestCase):
    def test_falls_back_to_username_without_first_name(self):
        user = User.objects.create_user('nofirstname', 'n@example.com', 'pw')
        self.assertEqual(str(user.profile), 'nofirstname')
