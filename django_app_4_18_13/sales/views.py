from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
import datetime
from api.views import current_time_aware, conv_to_js_date
from sales.models import *
from forms import *

from analysis.models import Cash_reserve, Search_history, Additional_capacity        
from api.views import gen_search_display

def hello(request):
    return HttpResponse("Hello")

def customer_signup(request, clean):
    if not clean and not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('login'))
    else:
        inputs = request.GET if request.GET else None 
        form = Customer_signup(inputs)     
        build = {'form': form, 'cust_title': "Customer Signup"}
        if (inputs) and form.is_valid():
            cd = form.cleaned_data
            try:
                find_cust = Customer.objects.get(email=cd['email'], password=cd['password'])
                build['error_message'] = 'The login/password combination is already registered in the system.'
                build['results'] = {'success': False, 'error': 'The login/password combination is already registered in the system.'}
            except:
                new_cust = Customer(first_name=cd['first_name'], last_name=cd['last_name'], email=cd['email'], password=cd['password'], reg_date=current_time_aware().date())
                new_cust.save() 
                build['results'] = {'success': True, 'first_name': cd['first_name'], 'last_name': cd['last_name'], 'email': cd['email']}
    return gen_search_display(request, build, clean)    


def purchase_option(request, clean):
    if not clean and not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('login'))
    else:
        inputs = request.GET if request.GET else None 
        form = Purchase_option(inputs)     
        build = {'form': form, 'cust_title': "Purchase option"}
            
        if (inputs) and form.is_valid():
            cd = form.cleaned_data
            try:
                find_cust = Customer.objects.get(email=cd['cust_email'], password=cd['cust_password'])
                find_org = Platform.objects.get(org_name=cd['org_name'])
                find_search = Search_history.objects.get(id=cd['search_id'])
    
                # raise error if id selected exists but refers to an search that resulted in an error or took place when no options were available for sale
                # or the purchase occured after too much time had passed, and the quoted price is deemed expired
                purch_date_time = current_time_aware()
                search_date_date = find_search.search_date
                expired = True if (purch_date_time - search_date_date) > datetime.timedelta(minutes = 10) else False            
                
                try:
                    existing = Contract.objects.get(search__id=cd['search_id'])
                except: 
                    pass
                else:
                    raise Exception
                
                if find_search.error or not find_search.get_status() or expired:
                    raise Exception
                
            except (Customer.DoesNotExist, Platform.DoesNotExist):
                build['error_message'] = 'The login/password and platform name combination is not valid.'
                build['results'] = {'success': False, 'error': 'The login/password and platform name combination is not valid.'}
            except (Search_history.DoesNotExist):
                build['error_message'] = 'The option id entered is not valid.'
                build['results'] = {'success': False, 'error': 'The option id entered is not valid.'}
            except (Exception):
                build['error_message'] = 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'
                build['results'] = {'success': False, 'error': 'The quoted price has expired or the related contract has already been purchased. Please run a new search.'}
            else:    
                new_contract = Contract(platform=find_org, customer=find_cust, purch_date=purch_date_time, search=find_search)
                new_contract.save()
                build['results'] = {'success': True, 'search_id': cd['search_id'], 'cust_email': cd['cust_email'], 'purchase_date': purch_date_time.strftime('%Y-%m-%d')}
                
                # augment cash reserve with option price and update option inventory capacity
                try:
                    latest_change = Cash_reserve.objects.latest('action_date')
                    new_balance = latest_change.cash_balance + new_contract.search.holding_price
                    add_cash = Cash_reserve(action_date=current_time_aware(), transaction=new_contract, cash_change=new_contract.search.holding_price, cash_balance=new_balance)
                    add_cash.save()
                    
                    capacity = Additional_capacity.objects.get(pk=1)
                    capacity.recalc_capacity(new_balance)
                    capacity.save()
                except:
                    pass
    
    return gen_search_display(request, build, clean)


def exercise_option(request, clean):
    if not clean and not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))
    else:
        inputs = request.GET if request.GET else None 
        form = Exercise_option(inputs)     
        build = {'form': form, 'cust_title': "Exercise option"}
            
        if (inputs) and form.is_valid():
            cd = form.cleaned_data
            try:
                find_cust = Customer.objects.get(email=cd['cust_email'], password=cd['cust_password'])
                find_org = Platform.objects.get(org_name=cd['org_name'])
                find_contract = Contract.objects.get(platform=find_org, customer=find_cust, search__id=cd['search_id'])  
            except (KeyError, Customer.DoesNotExist, Platform.DoesNotExist, Contract.DoesNotExist):
                build['error_message'] = 'The login/password, platform name, and transaction id combination is not valid.'
                build['results'] = {'success': False, 'error': 'The login/password, platform name, and transaction id combination is not valid.'}
                
            else:    
                if not find_contract.outstanding():
                    build['error_message'] = 'The contract selected is either expired or already exercised.'
                    build['results'] = {'success': False, 'error': 'The contract selected is either expired or already exercised.'}
                    
                else:
                    find_contract.ex_fare = cd['exercise_fare']
                    exercise_date_time = current_time_aware()
                    find_contract.ex_date = exercise_date_time
                    find_contract.save()
                    build['results'] = {'success': True, 'search_id': cd['search_id'], 'cust_email': cd['cust_email'], 'exercise_fare': cd['exercise_fare'], 'exercise_date': exercise_date_time.strftime('%Y-%m-%d')}
                    # augment cash reserve with option price
                    try:
                        if find_contract.ex_fare > find_contract.search.locked_fare:
                            effect = find_contract.search.locked_fare - find_contract.ex_fare
                            latest_change = Cash_reserve.objects.latest('action_date')    
                            new_balance = latest_change.cash_balance + effect                     
                            add_cash = Cash_reserve(action_date=current_time_aware(), transaction=find_contract, cash_change=effect, cash_balance=new_balance)
                            add_cash.save()
                            
                            capacity = Additional_capacity.objects.get(pk=1)
                            capacity.recalc_capacity(new_balance)
                            capacity.save()
                    except:
                        pass

    return gen_search_display(request, build, clean)