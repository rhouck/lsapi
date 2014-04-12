# Create your views here.

from promos.models import Contest

from api.views import gen_search_display
from api.utils import check_creds, current_time_aware

from pricing.utils import run_flight_search

import random
import datetime

from django.http import HttpResponse, Http404, HttpResponseRedirect
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



def contest(request):
	
	"""
	contest experience:
	user clicks to game, sees terms of game, previous contest results
		terms:
			what are the travel dates
			how much time until contest expires
			what are current flights
			how much is promo worth

		user submits email and guess
		limit to one guess per contest

	views:
	generate contest
	accept submissions
	send winner email


	models:
	contest
	submissions
	"""		
	if request.user.is_authenticated():
	    clean = False
	else:
	    clean = True

	clean = False
	if clean:
	    cred = check_creds(request.POST, Platform)
	    if not cred['success']:
	        return HttpResponse(json.encode(cred), mimetype="application/json")

	contest_length = 2
	promotion_value = 10

	current_time = current_time_aware()

	try:

		filt_date = (current_time-datetime.timedelta(days=contest_length+1))
		contest = Contest.objects.filter(expire_date__gte=filt_date)
		if contest:
			contest = contest.latest('expire_date')
			if contest.expire_date < current_time:
				contest = None

		# create new contest none exist or most recent has expired	
		if not contest:
			
			# select route
			origins = ['SFO', 'LAX', 'JFK', 'PHL', 'ORD']
			destinations = ['SFO', 'LAX', 'JFK', 'PHL', 'ATL', 'BOS', 'ORD', 'DFW', 'SAN', 'IAD']

			origin = random.choice(origins)
			if origin in destinations:
				destinations.remove(origin)
			destination = random.choice(destinations)    	

			# select travel dates
			current_date = current_time.date()

			depart_date = current_date + datetime.timedelta(days=random.randrange(21,40))
			return_date = depart_date + datetime.timedelta(days=random.randrange(2,20))

			contest = Contest(created_date=current_time, 
							expire_date=(current_time + datetime.timedelta(days=contest_length)), 
							origin_code=origin, 
							destination_code=destination,
							depart_date=depart_date,
							return_date=return_date,
							value=promotion_value)
			contest.save()


		# add try except if can't create contest
		results = contest.__dict__
		for i in ('id', '_state'):
			if i in results:
				del results[i]

	
		if not contest:
			raise Exception('No contest currently available. Please check again shortly')


	
		# build list of current flights
		res = run_flight_search(contest.origin_code, contest.destination_code, contest.depart_date, contest.return_date, 'any', 'any', 'any', 'any', cached=True)
		
		if res['success']:
			for i in ('success', 'min_flight', 'airlines'):
				del res[i]
			results['flights'] = res
			#return HttpResponse(json.encode(res), content_type="application/json")
		else:
			raise Exception('No contest currently available. Please check again shortly')

		results['success'] = True
	
	except Exception as err:
		results = {'success': False, 'error': err}

	return gen_search_display(request, {'results': results}, clean)
