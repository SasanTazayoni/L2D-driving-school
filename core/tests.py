from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from profiles.models import UserProfile


class Custom404Test(TestCase):
    """
    Tests for the custom 404 page.
    """
    def test_404_status_code(self):
        response = self.client.get('/this-page-does-not-exist/')
        self.assertEqual(response.status_code, 404)

    def test_404_uses_custom_template(self):
        response = self.client.get('/this-page-does-not-exist/')
        self.assertTemplateUsed(response, '404.html')


class HomeViewTest(TestCase):
    """
    Test to see if home page renders correctly.
    """
    def test_home_view(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')


class AppointmentsViewTest(TestCase):
    """
    Tests to see is appointments page works properly.
    """
    def setUp(self):
        self.client = Client()
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )

    def test_unauthenticated_user(self):
        """
        Testing unauthenticated user.
        """
        response = self.client.get(reverse('appointments'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/appointments/')

    def test_authenticated_user_with_unapproved_profile(self):
        """
        Testing authenticated, unapproved user.
        """
        self.client.login(username='fakeuser', password='password')
        response = self.client.get(reverse('appointments'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('contact'))

    def test_authenticated_user_with_approved_profile(self):
        """
        Testing authenticated, approved user.
        """
        self.client.login(username='fakeuser', password='password')

        self.testuser.profile.approved = True
        self.testuser.profile.save()

        response = self.client.get(reverse('appointments'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/appointments.html')
       

class ContactViewTest(TestCase):
    """
    Test to see if contact page renders correctly.
    """
    def test_contact_view(self):
        client = Client()
        response = client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')


class TermsAndConditionsViewTest(TestCase):
    """
    Test to see if terms and conditions page renders correctly.
    """
    def test_terms_view(self):
        from core.views import terms_and_conditions
        factory = RequestFactory()
        request = factory.get(reverse('terms'))
        response = terms_and_conditions(request)
        self.assertEqual(response.status_code, 200)


class CookiePolicyViewTest(TestCase):
    """
    Test to see if cookie policy page renders correctly.
    """
    def test_cookie_policy_view(self):
        from core.views import cookie_policy
        factory = RequestFactory()
        request = factory.get(reverse('cookie_policy'))
        response = cookie_policy(request)
        self.assertEqual(response.status_code, 200)


class PrivacyPolicyViewTest(TestCase):
    """
    Test to see if privacy policy page renders correctly.
    """
    def test_privacy_policy_view(self):
        from core.views import privacy_policy
        factory = RequestFactory()
        request = factory.get(reverse('privacy_policy'))
        response = privacy_policy(request)
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_response_time(self):
        """
        Privacy policy response should state one week turnaround.
        """
        from core.views import privacy_policy
        factory = RequestFactory()
        request = factory.get(reverse('privacy_policy'))
        response = privacy_policy(request)
        self.assertContains(response, 'one week')


class UserProfileSearchViewTest(TestCase):
    """
    Test user search on user profiles page.
    """
    def setUp(self):
        self.user1 = User.objects.create_user(
            first_name='John',
            username='johnsmith',
            email='john@example.com',
            password='password'
        )

        self.user2 = User.objects.create_user(
            first_name='Jane',
            username='janedoe',
            email='jane@example.com',
            password='password'
        )

    def test_search_bar_with_empty_query(self):
        url = reverse('user_profiles')
        response = self.client.get(url, {'search_query': ''})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No results found')

    def test_search_bar_with_results(self):
        url = reverse('user_profiles')
        response = self.client.get(url, {'search_query': 'John'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')


class UserProfilePaginationViewTest(TestCase):
    """
    Test pagination on user profiles page.
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.users = []

        for i in range(15):
            user = User.objects.create_user(
                first_name=f'User{i}',
                username=f'user_{i}',
                email=f'user_{i}@example.com',
                password='password'
            )

            profile, created = UserProfile.objects.get_or_create(user=user)
            self.users.append((user, profile))
    
    def test_pagination(self):
        url = reverse('user_profiles')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        user_profiles = UserProfile.objects.all().order_by('user__first_name')
        paginator = Paginator(user_profiles, 12)
        self.assertEqual(paginator.num_pages, 2)

    def test_empty_page_returns_last_page(self):
        """
        Test that requesting a page beyond the last page returns the last page.
        """
        url = reverse('user_profiles')
        response = self.client.get(url, {'page': 9999})
        self.assertEqual(response.status_code, 200)


class ProfileDetailViewTest(TestCase):
    """
    Test to see if user profile page renders correctly with a given id.
    """
    def setUp(self):
        self.testuser = User.objects.create_user(
            first_name='Fake',
            username='fakeuser',
            email='fakeuser@fakemail.com',
            password='password'
        )
        
        self.testuser_id = self.testuser.id

    def test_profile_detail_view(self):
        url = reverse('profile_detail', kwargs={'user_id': self.testuser.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/profile_detail.html')


class AboutMeEscapingTest(TestCase):
    """
    User-entered 'About me' text must be HTML-escaped (stored XSS guard)
    on both the public profile page and the user's own profile page.
    """
    payload = '<script>alert("xss")</script>\nSecond line'

    def setUp(self):
        self.user = User.objects.create_user(
            username='mallory', email='m@example.com', password='password'
        )
        profile = UserProfile.objects.get(user=self.user)
        profile.about_me = self.payload
        profile.save()

    def assert_escaped(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script>alert("xss")</script>')
        self.assertContains(
            response, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
        )
        self.assertContains(response, '<br>Second line')

    def test_public_profile_detail_escapes_about_me(self):
        response = self.client.get(
            reverse('profile_detail', args=[self.user.id])
        )
        self.assert_escaped(response)

    def test_own_profile_page_escapes_about_me(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile_page'))
        self.assert_escaped(response)



class SummernoteUploadDisabledTest(TestCase):
    """
    The summernote upload endpoint must refuse files from everyone, and the
    admin editor (which links to that endpoint) must still render.
    """
    def setUp(self):
        self.staff = User.objects.create_superuser(
            'boss', 'boss@example.com', 'password'
        )

    def post_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile('x.png', b'not really a png', 'image/png')
        return self.client.post(
            reverse('django_summernote-upload_attachment'), {'files': upload}
        )

    def test_anonymous_upload_refused(self):
        from django_summernote.models import Attachment
        self.assertEqual(self.post_file().status_code, 403)
        self.assertFalse(Attachment.objects.exists())

    def test_staff_upload_refused(self):
        from django_summernote.models import Attachment
        self.client.force_login(self.staff)
        self.assertEqual(self.post_file().status_code, 403)
        self.assertFalse(Attachment.objects.exists())

    def test_admin_editor_still_renders(self):
        self.client.force_login(self.staff)
        response = self.client.get('/admin/reviews/review/add/')
        self.assertEqual(response.status_code, 200)
