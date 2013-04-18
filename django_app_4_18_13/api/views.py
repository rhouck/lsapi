import datetime
import time
from django.utils.timezone import utc
import sys
from random import randint
import json

from django.template.loader import get_template
from django.template import Context 
from django.http import HttpResponse, Http404, HttpResponseRedirect 
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.template import RequestContext
from django.contrib import auth
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.views import logout
from django.contrib.auth.views import login

from forms import *

# this path contains all simualtion and valuation models and scripts
sys.path.insert(0, 'C:/Program Files (x86)/EasyPHP-5.3.4.0/www/SFmodel/analysis')
sys.path.insert(1, '/home/humbert/analysis')
sys.path.insert(2, '/home/develop/analysis')
sys.path.insert(3, '/home/bitnami/analysis')

def conv_to_js_date(date):
    return 1000 * time.mktime(date.timetuple())

def current_time_aware():
    return datetime.datetime.utcnow().replace(tzinfo=utc)

def gen_search_display(request, build, clean):    
    if clean: 
        if 'results' in build:
            if type(build['results']) is list:
                build['results'] = build['results'][0]
            return HttpResponse(json.dumps(build['results']), mimetype="application/json") 
        else:
            return render_to_response('blank.html')
    else:
        if 'results' in build:
            if type(build['results']) is not list:
                build['results'] = [build['results']]   
        return render_to_response('general_form.html', build, context_instance=RequestContext(request))
        

def hello(request):
    return HttpResponse(request.path)

@login_required()
def splash(request):
    return render_to_response('base.html')
    
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))
    
def login_view(request):
    inputs = request.POST if request.POST else None
    form = Login(inputs)     
    if (inputs) and form.is_valid():
        cd = form.cleaned_data
        user = auth.authenticate(username=cd['username'], password=cd['password'])
        if user is not None and user.is_active:
            auth.login(request, user)
            return render_to_response('base.html')
        else:
            form.invalid = "Sorry, that's not a valid username / password combination"  
            return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))
    else:
        return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))
    
    
