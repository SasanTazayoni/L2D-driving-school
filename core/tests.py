from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from profiles.models import UserProfile

User = get_user_model()


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
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/terms_and_conditions.html')


class CookiePolicyViewTest(TestCase):
    """
    Test to see if cookie policy page renders correctly.
    """
    def test_cookie_policy_view(self):
        response = self.client.get(reverse('cookie_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/cookie_policy.html')


class PrivacyPolicyViewTest(TestCase):
    """
    Test to see if privacy policy page renders correctly.
    """
    def test_privacy_policy_view(self):
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/privacy_policy.html')

    def test_privacy_policy_states_one_week_reply_time(self):
        """
        The privacy policy promises a reply to data requests within a week.
        """
        response = self.client.get(reverse('privacy_policy'))
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
        UserProfile.objects.update(approved=True)

    def test_search_bar_with_empty_query(self):
        url = reverse('user_profiles')
        response = self.client.get(url, {'search_query': ''})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No results found')

    def test_search_bar_with_results(self):
        url = reverse('user_profiles')
        response = self.client.get(url, {'search_query': 'John'})

        self.assertEqual(response.status_code, 200)
        names = [p.user.first_name for p in response.context['user_profiles']]
        self.assertEqual(names, ['John'])


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

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.approved = True
            profile.save()
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
        
        UserProfile.objects.filter(user=self.testuser).update(approved=True)
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
        profile.approved = True
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



class ProfileVisibilityTest(TestCase):
    """
    Only approved, non-staff profiles are public. Other profiles are hidden
    from the user list, the sitemap and their detail page (404), except to
    their owner and to staff.
    """
    def setUp(self):
        self.public = User.objects.create_user(
            'pub', 'pub@example.com', 'password', first_name='Publica')
        UserProfile.objects.filter(user=self.public).update(approved=True)
        self.pending = User.objects.create_user(
            'pend', 'pend@example.com', 'password', first_name='Pendina')
        self.admin = User.objects.create_superuser(
            'root', 'root@example.com', 'password', first_name='Rooty')
        UserProfile.objects.filter(user=self.admin).update(approved=True)

    def detail(self, user):
        return self.client.get(reverse('profile_detail', args=[user.id]))

    def test_user_list_shows_only_public_profiles(self):
        response = self.client.get(reverse('user_profiles'))
        names = [p.user.first_name for p in response.context['user_profiles']]
        self.assertEqual(names, ['Publica'])

    def test_unapproved_and_staff_profiles_are_404_to_the_public(self):
        self.assertEqual(self.detail(self.public).status_code, 200)
        self.assertEqual(self.detail(self.pending).status_code, 404)
        self.assertEqual(self.detail(self.admin).status_code, 404)

    def test_owner_can_view_own_unapproved_profile(self):
        self.client.force_login(self.pending)
        self.assertEqual(self.detail(self.pending).status_code, 200)

    def test_staff_can_view_any_profile(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.detail(self.pending).status_code, 200)

    def test_sitemap_lists_only_public_profiles(self):
        content = self.client.get('/sitemap.xml').content.decode()
        self.assertIn(reverse('profile_detail', args=[self.public.id]), content)
        self.assertNotIn(reverse('profile_detail', args=[self.pending.id]), content)
        self.assertNotIn(reverse('profile_detail', args=[self.admin.id]), content)

    def test_review_author_links_to_profile_only_when_public(self):
        from reviews.models import Review
        review = Review.objects.create(
            author=self.pending.profile, rating=5, content='x', approved=True)
        response = self.client.get(reverse('review_detail', args=[review.id]))
        self.assertContains(response, 'Pendina')
        self.assertNotContains(
            response, reverse('profile_detail', args=[self.pending.id]))



class ToastCloseButtonTest(TestCase):
    """
    Flash messages (toasts) have a close button that dismisses them.
    """
    def test_message_has_close_button(self):
        user = User.objects.create_user('toaster', 't@example.com', 'password')
        self.client.force_login(user)
        # An unapproved user visiting appointments gets an error message.
        response = self.client.get(reverse('appointments'), follow=True)
        self.assertContains(response, 'not currently authorised')
        self.assertContains(
            response,
            '<button type="button" class="btn-close" data-bs-dismiss="alert" '
            'aria-label="Close message"></button>',
            html=True,
        )



class SiteWideFrontEndTest(TestCase):
    """
    Site-wide front-end behaviour: navigation marks only the current page,
    toasts behave by severity, the home hero is visible straight away,
    search survives pagination, and forms guard against double submits.
    """
    def test_only_the_current_nav_link_is_marked_current(self):
        html = self.client.get(reverse('home')).content.decode()
        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertRegex(
            html, r'class="nav-link active" aria-current="page"\s+href="/"')

    def test_error_toast_stays_and_success_toast_fades(self):
        user = User.objects.create_user('toast', 't@example.com', 'Pass-word-123')
        # Error: unapproved user visiting appointments
        self.client.force_login(user)
        html = self.client.get(reverse('appointments'), follow=True).content.decode()
        self.assertRegex(html, r'class="alert [^"]*alert-danger"\s+role="alert"')
        self.assertNotRegex(html, r'alert-danger[^"]*auto-dismiss')
        self.client.logout()
        # Success: logging in
        html = self.client.post(
            reverse('account_login'),
            {'login': 'toast', 'password': 'Pass-word-123'}, follow=True,
        ).content.decode()
        self.assertRegex(
            html, r'class="alert [^"]*alert-success auto-dismiss"\s+role="status"')

    def test_home_hero_text_is_visible_immediately(self):
        html = self.client.get(reverse('home')).content.decode()
        self.assertIn('class="overlay active', html)
        self.assertNotIn('overlay.js', html)

    def test_pagination_links_keep_the_search(self):
        for i in range(14):
            User.objects.create_user(
                f'sam{i}', f'sam{i}@example.com', 'password', first_name=f'Sam{i}')
        UserProfile.objects.update(approved=True)
        html = self.client.get(
            reverse('user_profiles'), {'search_query': 'Sam'}).content.decode()
        self.assertIn('href="?search_query=Sam&amp;page=2"', html)
        self.assertNotIn('pagination.js', html)

    def test_auth_forms_guard_against_double_submit(self):
        for name in ('account_login', 'account_signup', 'account_reset_password'):
            html = self.client.get(reverse(name)).content.decode()
            self.assertIn('data-disable-on-submit', html, name)
            self.assertIn('js/disableSubmitButton.js', html, name)



class RobotsAndSitemapTest(TestCase):
    """
    robots.txt points crawlers at the real sitemap and blocks private areas;
    the sitemap lists public pages, approved reviews and public profiles only,
    on the domain stored in the Sites record.
    """
    def test_robots_txt(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        body = response.content.decode()
        self.assertIn('Sitemap: http://testserver/sitemap.xml', body)
        for private in ('/admin/', '/accounts/', '/profile/', '/appointments/'):
            self.assertIn(f'Disallow: {private}', body)
        self.assertNotIn('yourdomain.com', body)

    def test_sitemap_lists_public_content_on_the_site_domain(self):
        from django.contrib.sites.models import Site
        from reviews.models import Review
        Site.objects.filter(id=1).update(domain='l2d.example')
        Site.objects.clear_cache()  # Django caches the current Site in memory
        public = User.objects.create_user('pub', 'p@example.com', 'pw', first_name='Pub')
        UserProfile.objects.filter(user=public).update(approved=True)
        hidden = User.objects.create_user('hid', 'h@example.com', 'pw', first_name='Hid')
        shown = Review.objects.create(
            author=public.profile, rating=5, content='x', approved=True)
        pending = Review.objects.create(
            author=hidden.profile, rating=1, content='y', approved=False)

        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('<loc>http://l2d.example/</loc>', body)
        self.assertIn(reverse('review_detail', args=[shown.id]), body)
        self.assertNotIn(reverse('review_detail', args=[pending.id]), body)
        self.assertIn(reverse('profile_detail', args=[public.id]), body)
        self.assertNotIn(reverse('profile_detail', args=[hidden.id]), body)
        self.assertNotIn('example.com/', body)
