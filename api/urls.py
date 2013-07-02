from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf
from django.conf.urls.defaults import *
from api.views import *


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'^hello/$', hello),
    url(r'^$', splash),
    url(r'^accounts/login/$', login_view, name='login'),
    url(r'^accounts/logout/$', logout_view, name='logout'),

    # 'pricing' app urls
    url(r'^pricing/', include('pricing.urls')),

    # 'sales' app urls
    url(r'^sales/', include('sales.urls')),

    # 'analysis' app urls
    url(r'^analysis/', include('analysis.urls')),

)

