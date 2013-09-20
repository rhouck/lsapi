from settings import *


DEBUG = TEMPLATE_DEBUG = False

SITE_ID = 1

# cross domain xhr settings
XS_SHARING_ALLOWED_ORIGINS = 'http://beta.levelskies.com'
XS_SHARING_ALLOWED_METHODS = ['get','post']

if host == live:
    ADMINS = (
        ('sys admin', 'sysadmin@levelskies.com'),
    )

    MANAGERS = ADMINS

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'api',
            'USER': 'api',
            'PASSWORD': 'buttwatercruises',
            'HOST': '127.0.0.1',
            'PORT': ''
        }
    }
