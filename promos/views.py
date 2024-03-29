# Create your views here.

from promos.models import Contest, Submission, Promo
from promos.forms import ContestSubmissionForm, PromoDetail, CreatePromoForm

from api.views import gen_search_display
from api.utils import check_creds, current_time_aware, gen_alphanum_key

from pricing.utils import run_flight_search

from sales.models import Platform, Customer
from sales.utils import send_template_email

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

from django.contrib.auth.decorators import login_required

from django.template.defaultfilters import striptags


@login_required
def create_promo(request):

	inputs = request.POST if request.POST else None
	form = CreatePromoForm(inputs)
	build = {'form': form}

	if (inputs) and form.is_valid():
		cd = form.cleaned_data
		try:

			find_platform = Platform.objects.get(key=cd['platform_key'])
			find_cust = Customer.objects.get(email=cd['email'], platform=find_platform)
			new_promo = Promo(customer=find_cust, value=cd['value'], created_date= current_time_aware(), code=gen_alphanum_key())
			new_promo.save()

		except (Customer.DoesNotExist):
		    build['error_message'] = 'The customer is not registered.'
		    build['results'] = {'success': False, 'error': 'The customer is not registered.'}
		except (Platform.DoesNotExist):
		    build['error_message'] = 'The platform key is not valid.'
		    build['results'] = {'success': False, 'error': 'The platform key is not valid.'}
		except (Exception) as err:
		    build['error_message'] = '%s' % err
		    build['results'] = {'success': False, 'error': '%s' % err}
		else:

			results = new_promo.__dict__
			for i in ('id', 'customer_id', '_state'):
				if i in results:
					del results[i]
			if 'created_date' in results:
				results['created_date'] = str(results['created_date'])
			build['results'] = results
			build['results']['success'] = True	
	else:
		err_string = ""
		for error in form.errors.iteritems():
			err_string += "%s - %s " % (error[0], unicode(striptags(error[1]) if striptags else error[1]))

		build['results'] = {'success': False, 'error': err_string}
	
		
	return gen_search_display(request, build, False, method='post')



def promo_details(request):

	if request.user.is_authenticated():
	    clean = False
	else:
	    clean = True

	inputs = request.POST if request.POST else None	
	if clean:
	    cred = check_creds(request.POST, Platform)
	    if not cred['success']:
	        return HttpResponse(json.encode(cred), mimetype="application/json")

	form = PromoDetail(inputs)
	build = {'form': form}

	if (inputs) and form.is_valid():
		cd = form.cleaned_data

		try:

			find_platform = Platform.objects.get(key=cd['platform_key'])
			find_cust = Customer.objects.get(email=cd['email'], platform=find_platform)
			find_promo = Promo.objects.get(customer=find_cust, code=cd['code'])

			if find_promo.contract:
				raise Exception("Promotional code already used.")

		except (Customer.DoesNotExist):
		    build['error_message'] = 'The customer is not registered.'
		    build['results'] = {'success': False, 'error': 'The customer is not registered.'}
		except (Promo.DoesNotExist):
		    build['error_message'] = 'The promo code is not valid.'
		    build['results'] = {'success': False, 'error': 'The promo code is not valid.'}
		except (Exception) as err:
		    build['error_message'] = '%s' % err
		    build['results'] = {'success': False, 'error': '%s' % err}
		else:

			results = find_promo.__dict__
			for i in ('id', 'contract_id', 'customer_id', '_state'):
				if i in results:
					del results[i]
			if 'created_date' in results:
				results['created_date'] = str(results['created_date'])
			build['results'] = results
			build['results']['success'] = True	
	else:
		err_string = ""
		for error in form.errors.iteritems():
			err_string += "%s - %s " % (error[0], unicode(striptags(error[1]) if striptags else error[1]))

		build['results'] = {'success': False, 'error': err_string}
		
		
	return gen_search_display(request, build, clean, method='post')



def contest(request):
	
			
	if request.user.is_authenticated():
	    clean = False
	else:
	    clean = True

	
	if clean:
	    cred = check_creds(request.POST, Platform)
	    if not cred['success']:
	        return HttpResponse(json.encode(cred), mimetype="application/json")

	contest_length = 1
	promotion_value = 500

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

			# select decision time
			decision_times = [1,2,]
			decision_time = random.choice(decision_times)

			# select travel dates
			current_date = current_time.date()

			depart_date = current_date + datetime.timedelta(days=((decision_time*7)+ random.randrange(14,60)))
			return_date = depart_date + datetime.timedelta(days=random.randrange(2,20))

			contest = Contest(key=gen_alphanum_key(),
							created_date=current_time, 
							expire_date=(current_time + datetime.timedelta(days=contest_length)), 
							origin_code=origin, 
							destination_code=destination,
							decision_time=decision_time,
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

	# format date types for json 
	for k, v in results.iteritems():
		if isinstance(v, (datetime.date, datetime.datetime)):
			results[k] = str(v)		
	
	#return HttpResponse(json.encode(results), content_type="application/json")
	return gen_search_display(request, {'results': results}, clean, method='post')


def make_submission(request):
	
	if request.user.is_authenticated():
	    clean = False
	else:
	    clean = True

	inputs = request.POST if request.POST else None
	if clean:
	    cred = check_creds(request.POST, Platform)
	    if not cred['success']:
	        return HttpResponse(json.encode(cred), mimetype="application/json")


	form = ContestSubmissionForm(inputs)
	build = {'form': form}

	if (inputs) and form.is_valid():
		cd = form.cleaned_data
		
		try:

			find_platform = Platform.objects.get(key=cd['platform_key'])
			find_contest = Contest.objects.get(key=cd['contest_key'])

			# either find the existing customer associated with the platform and email addres or create it
			try:
			    find_cust = Customer.objects.get(email=cd['email'], platform=find_platform)
			except:
			    inps = {}
			    inps['key'] = gen_alphanum_key()
			    inps['reg_date'] = current_time_aware().date()
			    inps['platform'] = find_platform
			    inps['email'] = cd['email']
			    find_cust = Customer(**inps)
			    find_cust.save()
			    find_cust.create_highrise_account()

			find_cust.add_highrise_tag('contest')

			try:
				sub = Submission.objects.get(customer=find_cust, contest=find_contest)
			except:
				sub = Submission(contest=find_contest, customer=find_cust, created_date=current_time_aware(), value=cd['value'])
				sub.save()
			else:
				raise Exception("A submission has already been made to this contest with this email address.")

		except (Contest.DoesNotExist):
		    build['error_message'] = 'The contest key entered is not valid.'
		    build['results'] = {'success': False, 'error': 'The contest key entered is not valid.'}

		except (Exception) as err:
		    build['error_message'] = '%s' % err
		    build['results'] = {'success': False, 'error': 'Could not record your entry. %s' % err}

		else:

			# send email if subission successful
			subject = "We got your submission"
			title = "Now let's see how well you do..."
			
			if find_contest.decision_time == 1:
				time = "another week"
			elif find_contest.decision_time == 2:
				time = "another two weeks"
			elif find_contest.decision_time == 3:
				time = "another three weeks"
			elif find_contest.decision_time == 4:
				time = "another four weeks"
			else:
				time = "several days"
			
			body = "This contest is over soon but we won't know the final price of the flight for %s. When that happens we'll let you know if you won and earned a discount on your next Flex Fare. Don't worry, you don't have to wait long and you can enter the next contest as soon as it starts." % (time)
			try:
				send_template_email(sub.customer.email, subject, title, body)
			except:
				pass

			build['results'] = {'success': True}
	else:
		err_string = ""
		for error in form.errors.iteritems():
			err_string += "%s - %s " % (error[0], unicode(striptags(error[1]) if striptags else error[1]))

		build['results'] = {'success': False, 'error': err_string}
		
	return gen_search_display(request, build, clean, method='post')


def close_contests(request):


	if request.user.is_authenticated():
	    clean = False
	else:
	    clean = True

	inputs = request.POST if request.POST else None
	if clean:
	    cred = check_creds(request.POST, Platform)
	    if not cred['success']:
	        return HttpResponse(json.encode(cred), mimetype="application/json")


	current_time = current_time_aware()
	yesterday = current_time - datetime.timedelta(days=1)
	
	contests = Contest.objects.filter(closed=False)

	contest_data = []
	for i in contests:

		if i.end_price_date() < current_time and i.end_price_date() >= yesterday:

			contest_meta_data = {'key': i.key}

			subs = Submission.objects.filter(contest=i).order_by('created_date')
			contest_meta_data['subs'] = subs.count()
			
			if subs:

				# build list of current flights
				res = run_flight_search(i.origin_code, i.destination_code, i.depart_date, i.return_date, 'any', 'any', 'any', 'any', cached=True)	
				if res['success']:
					#return HttpResponse(json.encode(res), mimetype="application/json")
					i.end_price = res['min_fare']

			if not i.end_price:
				i.closed = True
				i.save()
			
			else:
				
				try:
					# find earliest-closest entry
					closest = None
					for k in subs:
						dif = abs(k.value-i.end_price)
						if not closest:
							closest = (k, dif)
						else:
							if dif < closest[1]:
								closest = (k, dif)

					# create promo for this user
					new_promo = Promo(customer=closest[0].customer, 
									created_date=current_time,
									value=i.value,
									code=gen_alphanum_key())
					new_promo.save()

					# send email
					subject = "You won the fare prediction contest!"
					title = "Dang, you are good."
					body = "You may remember entering a fare prediction contest on %s. We told you we'd let you know if your guess was closest to the actual fare and here we are. Also as promised, here's a promo code which let's you buy a Flex Fare for just $1:\n\n%s\n\nThe Level Skies Team" % (closest[0].created_date.strftime("%B %d"), new_promo.code)
					try:
						send_template_email(closest[0].customer.email, subject, title, body)
					except:
						pass

					# close contest
					i.closed = True
					i.save()

				except Exception as err:
					contest_meta_data['error'] = err
			
			contest_data.append(contest_meta_data)

	results = {'success': True, 'contest_data': contest_data}

	return gen_search_display(request, {'results': results}, clean, method='post')


