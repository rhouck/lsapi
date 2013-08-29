from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from routes.views import *

urlpatterns = patterns('',

    url(r'^hubs/$', hubs),
    url(r'^destinations/(?P<slug>[A-Z]{3})/$', dests),

)

