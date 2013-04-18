from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from pricing.views import *

urlpatterns = patterns('',
                       
    url(r'^hello/$', hello),
    url(r'^single/pretty/$', price_edu_combo(gen_search_display),{'clean': False}, name='price_single'),
    url(r'^single/$', price_edu_combo(gen_search_display),{'clean': True}),

)
    
