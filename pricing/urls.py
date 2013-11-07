from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from pricing.views import *

urlpatterns = patterns('',
    url(r'^flights/$', run_flight_search),
    #url(r'^single/demo/$', price_edu_combo,{'clean': False}, name='price_single'),
    url(r'^single/$', price_edu_combo, name='price_single'),
    url(r'^search/info/(?P<slug>[-\w]{6})/$', search_info, name='search_info'),
    url(r'^search/info/all/(?P<slug>[-\w]{6})/$', search_info,{'all': True}, name='search_info_all'),
    url(r'^search_results/$', demo_search_results),
    url(r'^search/flights/(?P<slug>[-\w]{6})/$', demo_search_results),
    url(r'^sky/$', test_skyscan),
    url(r'^wan/$', test_wan),
)

