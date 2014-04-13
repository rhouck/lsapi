from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

from sales.views import *

urlpatterns = patterns('',
    
    # sales
    url(r'^test/$', login_required(test_trans), name='test_trans'),
    url(r'^purchase/$', purchase_option, name='purchase'),
    url(r'^demo/$', demo_option, name='demo'),

    # staging - admin only
    url(r'^staging/$', login_required(get_staging_list), name='staging_view'),
    url(r'^staging/(?P<slug>[-\w]{6})/$', staged_item, name='staged_item'),
    url(r'^staging/add/(?P<action>[A-Za-z]{6,8})/(?P<slug>[-\w]{6})/$', add_to_staging, name='add_to_staging'),
    url(r'^staging/sweep/$', staging_sweep, name='staging_sweep'),

    # find and sign up customer - public
    url(r'^customer/find/$', find_cust_id, name='find_cust_id'),
    url(r'^customer/signup/$', customer_signup, name='cust_signup'),
    url(r'^customer/info/(?P<slug>[-\w]{6})/$', customer_info, name='customer_info'),
    url(r'^customer/open/(?P<slug>[-\w]{6})/$', find_open_contracts, name='open_contracts'),

    # view contracts - admin only
    url(r'^customer/$', login_required(get_cust_list), name='customer_list'),
    url(r'^customer/(?P<slug>[-\w]{6})/$', login_required(get_cust_detail), name='customer_detail'),
    url(r'^platform/$', login_required(get_plat_list), name='platform_list'),
    url(r'^platform/(?P<slug>[-\w]{6})/$', login_required(get_plat_detail), name='platform_detail'),

    url(r'^alerts/$', alerts, name='alerts_sweep'),

)
