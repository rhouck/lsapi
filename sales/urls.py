from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

from sales.views import *

urlpatterns = patterns('',

    url(r'^purchase/$', purchase_option, name='purchase'),
    url(r'^exercise/$', exercise_option, name='exercise'),
    url(r'^customer/find/$', find_cust_id, name='find_cust_id'),
    url(r'^customer/signup/$', customer_signup, name='cust_signup'),
    url(r'^customer/open/$', customer_login, name='customer_login'),
    url(r'^customer/open/(?P<slug>[-\w]{6})/$', find_open_contracts, name='open_contracts'),
    url(r'^customer/$', login_required(CustomerList.as_view()), name='customer_list'),
    url(r'^customer/(?P<slug>[-\w]{6})/$', login_required(CustomerDetail.as_view()), name='customer_detail'),
    url(r'^platform/$', login_required(PlatformList.as_view()), name='platform_list'),
    url(r'^platform/(?P<slug>[-\w]{6})/$', PlatformDetail.as_view(), name='platform_detail'),
    url(r'^platform/(?P<slug_2>[-\w]{6})/customer/(?P<slug>[-\w]{6})/$', find_open_contracts, name='platform_specific_customer_detail'),
    url(r'^customer/contact/(?P<slug>[-\w]{6})/$', CustomerContact.as_view(), name='customer_contact'),

)
