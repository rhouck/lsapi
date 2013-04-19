from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

from sales.views import *

urlpatterns = patterns('',

    url(r'^purchase/pretty/$', purchase_option, {'clean': False}, name='purchase'),
    url(r'^purchase/$', purchase_option, {'clean': True}),
    url(r'^exercise/pretty/$', exercise_option, {'clean': False}, name='exercise'),
    url(r'^exercise/$', exercise_option, {'clean': True}),
    url(r'^customer/signup/pretty/$', customer_signup, {'clean': False}, name='cust_signup'),
    url(r'^customer/signup/$', customer_signup, {'clean': True}),
    
    url(r'^customer/(?P<pk>\d+)/$', 
        login_required(
            DetailView.as_view(
                model = Customer,
                context_object_name = "name",
                template_name='sales/org_detail.html'),), 
        name='customer_detail'),
    url(r'^platform/(?P<pk>\d+)/$', 
        login_required(
            DetailView.as_view(
                model = Platform,
                context_object_name = "name",
                template_name='sales/org_detail.html'),), 
        name='platform_detail'),

)
