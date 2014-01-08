import sys

STATIC_URL = 'https://api.dev.levelskies.com/static/'

STATIC_ROOT = '/home/projects/api.dev.levelskies.com/static/'

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
        'NAME': 'api_dev',
        'USER': 'api_dev',
        'PASSWORD': 'Ziggity_0*9bomb_dev',
        'HOST': '10.55.83.134',
        'PORT': ''
    }
}

mongo_host = 'localhost'
mongo_port = 27017

sys.path.insert(0, '/home/projects/dev-pricing-model')
