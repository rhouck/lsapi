from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from pricing.views import *

urlpatterns = patterns('',

    url(r'^single/demo/$', price_edu_combo(gen_search_display),{'clean': False}, name='price_single'),
    url(r'^single/$', price_edu_combo(gen_search_display),{'clean': True}),
    url(r'^search/info/(?P<slug>[-\w]{6})/$', search_info, name='search_info'),
    url(r'^search/info/all/(?P<slug>[-\w]{6})/$', search_info,{'all': True}, name='search_info'),
)

