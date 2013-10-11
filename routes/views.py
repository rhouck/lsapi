from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.template import RequestContext

import json
from routes.models import *

def hubs(request):
    res = Routes.objects.values("org_code").distinct()
    bank = [i['org_code'] for i in res]
    bank.sort()
    return HttpResponse(json.dumps({'hubs': bank}), mimetype="application/json")

def dests(request, slug):
    res = Routes.objects.filter(org_code=slug).values("dest_code")
    bank = [i['dest_code'] for i in res]
    bank.sort()
    return HttpResponse(json.dumps({'destinations': bank}), mimetype="application/json")


def pairs(request):
    res = Routes.objects.all().order_by('org_code', 'dest_code')
    bank = [{'hub': i.org_code, 'destination': i.dest_code} for i in res]
    return HttpResponse(json.dumps({'pairs': bank}), mimetype="application/json")
