from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from promos.views import *

urlpatterns = patterns('',

    url(r'^contest/$', contest, name='contest'),
    url(r'^submission/$', make_submission, name='submission'),
    url(r'^details/$', promo_details, name='promo_details'),


)

