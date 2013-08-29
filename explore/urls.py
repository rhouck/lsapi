from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from explore.views import *

urlpatterns = patterns('',

    url(r'^hello/$', hello),
    url(r'^changes/$', fare_changes),




)

