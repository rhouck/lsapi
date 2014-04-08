from django.conf.urls.defaults import patterns, include, url
from django.core.context_processors import csrf

from analysis.views import *

urlpatterns = patterns('',

    url(r'^historical/date/$', historical, {'departure_trend': None}, name='hist_date'),
    url(r'^historical/trend/absolute/$', historical, {'departure_trend': 'absolute'}, name='hist_trend_abs'),
    url(r'^historical/trend/relative/$', historical, {'departure_trend': 'relative'}, name='hist_trend_rel'),
    url(r'^projection/date/$', projections, {'format': 'date'}, name='proj_date'),
    url(r'^projection/departure/$', projections, {'format': 'departure'}, name='proj_depart'),
    url(r'^projection/overlay/absolute/$', overlay, {'departure_trend': 'absolute'}, name='proj_accuracy_abs'),
    url(r'^projection/overlay/relative/$', overlay, {'departure_trend': 'relative'}, name='proj_accuracy_rel'),
    url(r'^simulation/sales/$', simulation_sales, name='sim_analysis'),
    url(r'^dashboard/$', exposure, name='dashboard'),
    url(r'^status/$', replicated_db_status, name='rep_data_status'),

    url(r'^performance/$', perf, name='perf'),


)

