"""
Point Django's "Sites" record at the real website instead of the default
example.com. The sitemap builds its links from this record, and allauth uses
its name to prefix email subjects ("[L2D Driving School] Password Reset").

The domain comes from the HOST environment variable (set on Heroku and in
env.py); when HOST isn't set, e.g. in the test runner, nothing is changed.
"""
import os

from django.conf import settings
from django.db import migrations


def set_site_domain(apps, schema_editor):  # pylint: disable=unused-argument
    host = os.environ.get("HOST")
    if not host:
        return
    Site = apps.get_model("sites", "Site")
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={"domain": host, "name": "L2D Driving School"},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(set_site_domain, migrations.RunPython.noop),
    ]
