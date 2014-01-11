import datetime
import time
import sys
try:
    import czjson as json
    json.encode = json.dumps
    json.decode = json.loads
except ImportError:
    try:
        import cjson as json
    except ImportError:
        import json
        json.encode = json.dumps
        json.decode = json.loads

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
from utils import *


from django.core.mail import send_mail

def email_template(request):
    
    send_mail('Just added to staging',
    'lksadjf',
    'sysadmin@levelskies.com',
    ['ryank@levelskies.com'],
    fail_silently=False)
    
    """
    send_mail("subject",
    "message",
    'sales@levelskies.com',
    ['%s' % ('ryanchouck@gmail.com')],
    fail_silently=False,
    auth_user='sales@levelskies.com',
    auth_password='_second&mission_')
    """
    
    build = {'title': 'test title', 'body': 'test body copy'}
    return render_to_response('email_template/index.html', build, context_instance=RequestContext(request))

    



def gen_search_display(request, build, clean, method=None):
    if 'results' in build:
        if type(build['results']) is list:
            build['results'] = build['results'][0]
    if clean:
        if 'results' in build:
            return HttpResponse(json.encode(build['results']), mimetype="application/json")
        else:
            return render_to_response('blank.html')
    else:
        if method == 'post':
            return render_to_response('general_form_post.html', build, context_instance=RequestContext(request))
        else:
            return render_to_response('general_form.html', build, context_instance=RequestContext(request))


def hello(request):
    url = "https://www.google.com/"
    ex = {'url': url}
    return HttpResponse(json.encode(ex), mimetype="application/json")
    # return HttpResponse(request.path)


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
        user = auth.authenticate(
            username=cd['username'], password=cd['password'])
        if user is not None and user.is_active:
            auth.login(request, user)
            #return render_to_response('base.html')
            return HttpResponseRedirect(reverse('fare_changes'))
        else:
            form.invalid = "Sorry, that's not a valid username / password combination"
            return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))
    else:
        return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))
