# -*- coding: utf-8 -*-
def pytest_configure():
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        REST_FRAMEWORK={
            "PAGE_SIZE": 10
        },
        SECRET_KEY="not very secret in tests",
        USE_I18N=True,
        USE_L10N=True,
        USE_TZ=True,
        INSTALLED_APPS=(
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.admin",
            "django.contrib.sites",
            "rest_framework",
            "fdadb"
        ),
        ROOT_URLCONF="fdadb.api_urls",
        TESTING=True,

        ENV_PREFIX="test-env",
    )
