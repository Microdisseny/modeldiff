# -*- coding: utf8 -*-
from __future__ import unicode_literals

import os
import sys
import argparse
from django.conf import settings
import django


class QuickDjangoTest(object):
    """
    A quick way to run the Django test suite without a fully-configured project.

    Example usage:

        >>> QuickDjangoTest(apps=['app1', 'app2'], db='sqlite')

    Based on a script published by Lukasz Dziedzia at:
    http://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app
    """
    DIRNAME = os.path.dirname(__file__)
    INSTALLED_APPS = [
        'django.contrib.staticfiles',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
    ]
    SPATIALITE_LIBRARY_PATH = 'mod_spatialite.so'
    if django.VERSION >= (1, 8, 0):
        TEMPLATES = {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                ]
            },
            'APP_DIRS': True,
        }

    def __init__(self, *args, **kwargs):
        self.apps = kwargs.get('apps', [])
        self.database= kwargs.get('db', 'sqlite')
        self.run_tests()

    def run_tests(self):
        """
        Fire up the Django test suite developed for version 1.2
        """
        if self.database == 'postgres':
            databases = {
                'default': {
                    'ENGINE': 'django.contrib.gis.db.backends.postgis',
                    'NAME': 'modeldiff_test',
                    'HOST': '127.0.0.1',
                    'USER': 'admin',
                    'PASSWORD': 'p1234',
                }
            }

        else:
            databases = {
                'default': {
                     'ENGINE': 'django.contrib.gis.db.backends.spatialite',
                     'NAME': os.path.join(self.DIRNAME, 'database.db'),
                }
            }
        conf = {
            'DATABASES': databases,
            'INSTALLED_APPS': self.INSTALLED_APPS + self.apps,
            'STATIC_URL': '/static/',
        }
        if 'SPATIALITE_LIBRARY_PATH' in os.environ:
            # If you get SpatiaLite-related errors, refer to this document
            # to find out the proper SPATIALITE_LIBRARY_PATH value
            # for your platform.
            # https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/spatialite/
            #
            # Example for macOS (with spatialite-tools installed using brew):
            # $ export SPATIALITE_LIBRARY_PATH='/usr/local/lib/mod_spatialite.dylib'
            conf['SPATIALITE_LIBRARY_PATH'] = os.getenv('SPATIALITE_LIBRARY_PATH')
        if django.VERSION >= (1, 8, 0):
            conf['TEMPLATES'] = self.TEMPLATES,
        settings.configure(**conf)
        if django.VERSION >= (1, 7, 0):
            # see: https://docs.djangoproject.com/en/dev/releases/1.7/#standalone-scripts
            django.setup()
        if django.VERSION >= (1, 6, 0):
            # see: https://docs.djangoproject.com/en/dev/releases/1.6/#discovery-of-tests-in-any-test-module
            from django.test.runner import DiscoverRunner as Runner
        else:
            from django.test.simple import DjangoTestSuiteRunner as Runner

        failures = Runner().run_tests(self.apps, verbosity=1)
        if failures:  # pragma: no cover
            sys.exit(failures)

if __name__ == '__main__':
    """
    What do when the user hits this file from the shell.

    Example usage:

        $ python quicktest.py app1 app2 --db=sqlite

    """
    parser = argparse.ArgumentParser(
        usage="[args] [--db=sqlite]",
        description="Run Django tests on the provided applications."
    )
    parser.add_argument('apps', nargs='+', type=str)
    parser.add_argument('--db', nargs='?', type=str, default='sqlite')
    args = parser.parse_args()
    QuickDjangoTest(apps=args.apps, db=args.db)
