from sales.models import *
from api.utils import current_time_aware, conv_to_js_date, gen_alphanum_key, check_creds, run_authnet_trans, test_trans

# maybe don't need anymore
from django.core.mail import send_mail, get_connection
#from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

from api.settings import FROM_EMAIL_1, FROM_EMAIL_1_PASSWORD

def send_template_email(to_email, subject, title, body, table=None):


    plaintext = get_template('email_template/plain_text.txt')
    htmly     = get_template('email_template/index.html')
    d = Context({'title': title, 'body': body, 'table': table})
    text_content = plaintext.render(d)
    html_content = htmly.render(d)



    connection = get_connection(username=FROM_EMAIL_1, password=FROM_EMAIL_1_PASSWORD, fail_silently=False)
    msg = EmailMultiAlternatives(subject, text_content, FROM_EMAIL_1, [to_email], connection=connection)
    msg.attach_alternative(html_content, "text/html")
    msg.send()



def exercise_option(cust_key, search_key, exercise, inputs, use_gateway=True, promo=None):

    # fare=None, dep_date=None, ret_date=None, flight_purchased=None, notes=None,

    build = {}

    try:

        find_cust = Customer.objects.get(key__iexact=cust_key)
        find_contract = Contract.objects.get(customer=find_cust, search__key=search_key)

    except (KeyError, Customer.DoesNotExist, Contract.DoesNotExist):
        build['error_message'] = 'The user id and/or transaction id is not valid.'
        build['results'] = {'success': False, 'error': 'The user id and/or transaction id is not valid.'}

    else:
        if find_contract.expired() and exercise:
            build['error_message'] = 'The contract selected is expired and connot be converted into a ticket.'
            build['results'] = {'success': False, 'error': 'The contract selected is expired and connot be converted into a ticket.'}
        elif find_contract.close_staged_date:
            build['error_message'] = 'The contract has already been closed.'
            build['results'] = {'success': False, 'error': 'The contract has already been closed.'}
        else:
            if exercise:
                # if option is converted into airline ticket
                find_contract.ex_fare = inputs['fare']
                find_contract.dep_date = inputs['dep_date']
                find_contract.ret_date = inputs['ret_date']
                find_contract.flight_purchased = inputs['flight_purchased']
                find_contract.notes = inputs['notes']
                """
                # set traveler information from staging model to contract model
                for t in('traveler_first_name','traveler_middle_name','traveler_last_name','traveler_infant','traveler_gender','traveler_birth_date','traveler_passport_country','traveler_seat_pref','traveler_rewards_program','traveler_contact_email',):
                    try:
                        setattr(find_contract, t, inputs[t])
                    except:
                        pass

                # refund partial value if exercised fare below refund value
                if find_contract.search.locked_fare > inputs['fare'] and use_gateway:
                    card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': str(find_contract.cc_last_four).zfill(4), 'month': find_contract.cc_exp_month, 'year': find_contract.cc_exp_year}
                    response = run_authnet_trans(find_contract.search.locked_fare - inputs['fare'], card_info, trans_id=find_contract.gateway_id)
                    if not response['success']:
                        build['results'] = {'success': False, 'error': response['status']}
                        return build
                """
            else:
                # if option is refunded
                if use_gateway:
                    
                    if promo:
                        if find_contract.search.holding_price > promo:
                            amount = find_contract.search.holding_price - promo
                        else:
                            amount = 1

                    card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': str(find_contract.cc_last_four).zfill(4), 'month': find_contract.cc_exp_month, 'year': find_contract.cc_exp_year}
                    response = run_authnet_trans(amount, card_info, trans_id=find_contract.gateway_id)
                else:
                    response = {'success': True}
                if not response['success']:
                    build['results'] = {'success': False, 'error': response['status']}
                    return build


                find_contract.ex_fare = None
                find_contract.dep_date = None
                find_contract.ret_date = None
                find_contract.flight_purchased = None
                find_contract.notes = inputs['notes']


            exercise_date_time = current_time_aware()
            find_contract.close_staged_date = exercise_date_time
            find_contract.save()
            build['results'] = {'success': True, 'search_key': search_key, 'cust_key': cust_key, 'exercise_fare': find_contract.ex_fare, 'exercise_date': exercise_date_time.strftime('%Y-%m-%d')}

            # augment cash reserve with option price
            try:
                if find_contract.ex_fare > find_contract.search.locked_fare:
                    effect = find_contract.search.locked_fare - find_contract.ex_fare
                elif not exercise:
                    effect = -1 * find_contract.search.holding_price
                else: 
                    effect = None

                if effect:
                    latest_change = Cash_reserve.objects.latest('action_date')
                    new_balance = latest_change.cash_balance + effect
                    add_cash = Cash_reserve(action_date=current_time_aware(), transaction=find_contract, cash_change=effect, cash_balance=new_balance)
                    add_cash.save()

                    capacity = Additional_capacity.objects.get(pk=1)
                    capacity.recalc_capacity(new_balance)
                    capacity.save()
            except:
                pass


    return build
    

