
DEBUG = TEMPLATE_DEBUG = True

SITE_ID = 1

# cross domain xhr settings
#XS_SHARING_ALLOWED_ORIGINS = 'http://beta.levelskies.com'
#XS_SHARING_ALLOWED_METHODS = ['get','post']

ADMINS = (
    ('sys admin', 'sysadmin@levelskies.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'api',
        'USER': 'api',
        'PASSWORD': 'Ziggity_0*9bomb',
        'HOST': '10.55.83.134',
        'PORT': ''
    }
}
