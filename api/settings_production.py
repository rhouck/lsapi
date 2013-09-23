
DEBUG = TEMPLATE_DEBUG = True

SITE_ID = 1

# cross domain xhr settings
XS_SHARING_ALLOWED_ORIGINS = ['http://beta.levelskies.com','http://api.levelskies.net']
XS_SHARING_ALLOWED_METHODS = ['get','post']


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
        'HOST': 'localhost',
        'PORT': ''
    }
}
