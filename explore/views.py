from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.template import RequestContext
import sys
sys.path.insert(0, '/home/projects/api')
from api.views import current_time_aware, conv_to_js_date
from view_data import *
from forms import *



def hello(request):
    #return HttpResponse(json.dumps(ex), mimetype="application/json")
    return HttpResponse("hello")

def fare_changes(request):

  inputs = request.GET if request.GET else None
  form = FareChanges(inputs)

  if (inputs) and form.is_valid():

    depart_length =[0,1000]
    date_completed=[datetime.date(2000,1,1), datetime.date(3000,1,1)]
    dep_wkday = None
    ret_wkday = None

    cd = form.cleaned_data
    if cd['min_dep_len']:
      depart_length[0] = cd['min_dep_len']
    if cd['max_dep_len']:
      depart_length[1] = cd['max_dep_len']
    if cd['min_date_comp']:
      date_completed[0] = cd['min_date_comp']
    if cd['max_date_comp']:
      date_completed[1] = cd['max_date_comp']
    if cd['proj_int']:
      proj_interval = cd['proj_int']
    if cd['dep_wkday']:
      dep_wkday = cd['dep_wkday']
    if cd['ret_wkday']:
      ret_wkday = cd['ret_wkday']

    dist = FareMovement(route=cd['route'], depart_length=depart_length, date_completed=date_completed, proj_interval=proj_interval, dep_wkday=dep_wkday, ret_wkday=ret_wkday)
    dist.gen_dist()
    res = dist.data_bank

    return render_to_response('explore/fare_changes.html', {'form': form, 'res': res}, context_instance=RequestContext(request))

  else:
    return render_to_response('explore/fare_changes.html', {'form': form,}, context_instance=RequestContext(request))

