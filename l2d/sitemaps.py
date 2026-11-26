from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from reviews.models import Review
from profiles.models import UserProfile


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'

    PAGES = {
        'home': 1.0,
        'reviews': 0.9,
        'contact': 0.7,
        'privacy_policy': 0.3,
        'terms': 0.3,
        'cookie_policy': 0.3,
    }

    def items(self):
        return list(self.PAGES.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.PAGES[item]


class ReviewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Review.objects.filter(approved=True)

    def location(self, item):
        return reverse('review_detail', args=[item.id])

    def lastmod(self, item):
        return item.updated_on or item.created_on


class ProfileSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return (
            UserProfile.objects.public()
            .select_related('user')
            .order_by('id')
        )

    def location(self, item):
        return reverse('profile_detail', args=[item.user.id])

    def lastmod(self, item):
        return item.created_on
