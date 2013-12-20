# Django settings for api project.
import os.path
from socket import gethostname
import sys
host = gethostname()
live = 'scheduler.levelskies.com'
mongo_host = 'localhost'
mongo_port = 27017

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Ryan Houck', 'ryan@levelskies.com'),
)

MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'America/Los_Angeles'
TIME_ZONE = None

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 2

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ('assets', os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'assets'))),
    os.path.join(BASE_DIR, 'assets/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1l1b55_*(3f7=2ruge%85k9%ns75!3cx^#tw@(!*wlkb+s@1^w'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # custom middleware
    #'django.middleware.custom.django-crossdomainxhr-middleware',
    'middleware.cdxhr.XsSharing',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'api.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'api.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'django.contrib.redirects',

    # tools
    #'tastypie',
    'south',
    'widget_tweaks',
    #'debug_toolbar',
    # custom apps
    'pricing',
    'sales',
    'analysis',
    'routes',


)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# this path contains all simualtion and valuation models and scripts
sys.path.insert(0, 'C:/Program Files (x86)/EasyPHP-DevServer-13.1VC9/data/localweb/projects/analysis')
sys.path.insert(1, '/home/humbert/analysis')
sys.path.insert(2, '/home/develop/analysis')
sys.path.insert(3, '/home/bitnami/analysis')
sys.path.insert(4, '/home/projects/api')



# cross domain xhr settings
XS_SHARING_ALLOWED_ORIGINS = '*'
#XS_SHARING_ALLOWED_ORIGINS = "http://127.0.0.1:8000"
XS_SHARING_ALLOWED_METHODS = ['POST','GET','OPTIONS', 'PUT', 'DELETE']
XS_SHARING_ALLOWED_HEADERS = ['Origin', 'Content-Type', 'Accept']
XS_SHARING_ALLOWED_CREDENTIALS = 'true'


# email setup
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
EMAIL_HOST_USER = 'sysadmin@levelskies.com'
EMAIL_HOST_PASSWORD = 'buttwatercruises'
#EMAIL_SUBJECT_PREFIX = 'Level Skies - '
DEFAULT_FROM_EMAIL = 'sysadmin@levelskies.com'




# for debug toolbar
#INTERNAL_IPS = ('127.0.0.1',)

# Use site-specific settings
local_settings_path = os.path.join(os.path.dirname(__file__), 'local_settings.py')
if host == live:
    from settings_production import *
else:
    from local_settings import *
