from inlinestyler.utils import inline_css

from django.db.models import Q

from sales.models import *
from api.utils import current_time_aware, conv_to_js_date, gen_alphanum_key, check_creds, run_authnet_trans, test_trans
from api.settings import HIGHRISE_CONFIG
# maybe don't need anymore
from django.core.mail import send_mail, get_connection
#from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

from api.settings import FROM_EMAIL_1, FROM_EMAIL_1_PASSWORD

from promos.models import Submission


from billdotcom.session import Session
from billdotcom.bill import Bill, BillLineItem
from billdotcom.vendor import Vendor

import datetime
import random


def highrise_cust_setup():

    # run to build highrise customer ids and add appropriate tags to existing customers in api db

    no_ids = Customer.objects.filter(Q(highrise_id=None) | Q(highrise_id=""))

    new_ids = []
    customer_tags = []
    demo_tags = []
    contest_tags = [] 
    for ind, i in enumerate(no_ids):
        
        # create highrise id
        i.create_highrise_account()
        i.save()

        new_ids.append(i.email)    
        
        # check if customer has purchased contract
        contracts = Contract.objects.filter(customer=i)
        if contracts:
            i.add_highrise_tag('customer')
            customer_tags.append(i.email)

        # check if customer has signed up for demo
        demos = Demo.objects.filter(customer=i)
        if demos:
            i.add_highrise_tag('demo')
            demo_tags.append(i.email)

        # check if customer has submitted contest entry
        entries = Submission.objects.filter(customer=i)
        if entries:
            i.add_highrise_tag('contest')
            contest_tags.append(i.email)
    

    return {'new_highrise_ids': new_ids, 'customer_tags': customer_tags, 'demo_tags': demo_tags, 'contest_tags': contest_tags}


def send_template_email(to_email, subject, title, body, table=None):

    
    
    plaintext = get_template('email_template/plain_text.txt')
    htmly     = get_template('email_template/index.html')
    d = Context({'title': title, 'body': body, 'table': table})
    text_content = plaintext.render(d)
    html_content = htmly.render(d)
    
    html_content = inline_css(html_content)

    connection = get_connection(username=FROM_EMAIL_1, password=FROM_EMAIL_1_PASSWORD, fail_silently=False)
    msg = EmailMultiAlternatives(subject, text_content, FROM_EMAIL_1, [to_email], [HIGHRISE_CONFIG['email']], connection=connection)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def add_to_billdotcom(customer, contract, amount):

    try:

        with Session() as s:

            # create or find Vendor

            activity = ""

            mid = "" if not contract.billing_middle_name else "%s " % (contract.billing_middle_name)
            name = "%s %s%s" % (contract.billing_first_name, mid, contract.billing_last_name)
            shortName = "%s, %s." % (contract.billing_last_name, contract.billing_first_name[0])

            billdotcom_id = customer.billdotcom_id if customer.billdotcom_id else None
            
            if not billdotcom_id:

                a = Vendor(name=name,
                            shortName=shortName,
                            nameOnCheck=name,
                            address1=contract.shipping_address1,
                            address2=contract.shipping_address2,
                            addressCity=contract.shipping_city,
                            addressState=contract.shipping_province,
                            addressZip=contract.shipping_postal_code,
                            addressCountry=contract.shipping_country,
                            email=customer.email,
                            )
                a['id'] = s.create(a)
                billdotcom_id = a['id']
                vendor = s.read('Vendor', id=billdotcom_id)

                # save update customer model with billdotcom_id
                customer.billdotcom_id = billdotcom_id
                customer.save()

                activity += "Created vendor: %s. " % (a['id'])
            
            else:
                
                vendor = s.read('Vendor', id=billdotcom_id)
                if vendor:
                    vendor['name'] =name
                    vendor['shortName'] =shortName
                    vendor['nameOnCheck'] =name
                    vendor['address1'] = contract.shipping_address1
                    vendor['address2'] = contract.shipping_address2
                    vendor['addressCity'] = contract.shipping_city
                    vendor['addressState'] = contract.shipping_province
                    vendor['addressZip'] = contract.shipping_postal_code
                    vendor['addressCountry'] = contract.shipping_country
                    vendor['email'] = customer.email
                    s.update(vendor)
                
                    activity += "Updated vendor : %s. " % (billdotcom_id)
                else:
                    raise Exception("billdotcom_id did not return any registered vendors.")


            
            # create new bill object
            invoice_no = contract.search.key
            today = current_time_aware().date()

            b = Bill(
                vendorId = billdotcom_id,
                invoiceNumber = invoice_no,
                invoiceDate = today,
                dueDate = today,
                #amount = amount
            )
            b.add_line_item(BillLineItem(amount=amount, description="Flex Fare airfare protection"))
            b['id'] = s.create(b)
            
            activity += "Creaed bill: %s" % (b['id'])
            
            bill = s.read('Bill', id=b['id'])
            
            if not bill:
                raise Exception("Could not create new bill.")
        
        return {'success': True, 'activity': activity}
    
    except Exception as err:
        
        return {'success': False, 'error': err}




def exercise_option(cust_key, search_key, exercise, inputs, use_gateway=True, promo=None, payout=None):

    # fare=None, dep_date=None, ret_date=None, flight_purchased=None, notes=None,

    build = {}

    try:

        find_cust = Customer.objects.get(key__iexact=cust_key)
        find_contract = Contract.objects.get(customer=find_cust, search__key=search_key)

    except (KeyError, Customer.DoesNotExist, Contract.DoesNotExist):
        build = {'success': False, 'error': 'The user id and/or transaction id is not valid.'}

    else:
        
        if find_contract.close_staged_date:
            build = {'success': False, 'error': 'The contract has already been closed.'}
        else:
            if exercise:
                # if option is converted into airline ticket
                find_contract.ex_fare = inputs['fare']
                find_contract.dep_date = inputs['dep_date']
                find_contract.ret_date = inputs['ret_date']
                find_contract.flight_purchased = inputs['flight_purchased']
                find_contract.notes = inputs['notes']
                

                # add payment to bill.com if low fares have increased
                if payout:
                    response = add_to_billdotcom(find_cust, find_contract, payout)
                    if not response['success']:
                        build = {'success': False, 'error': response['error']}
                        return build
            else:
                # if option is refunded
                if use_gateway:
                    
                    amount = find_contract.search.holding_price
                    if promo:
                        if amount > promo:
                            amount = amount - promo
                        else:
                            amount = 1

                    card_info = {'first_name': find_cust.first_name, 'last_name': find_cust.last_name, 'number': str(find_contract.cc_last_four).zfill(4), 'month': find_contract.cc_exp_month, 'year': find_contract.cc_exp_year}
                    response = run_authnet_trans(amount, card_info, trans_id=find_contract.gateway_id)
                    
                else:
                    response = {'success': True}
                
                if not response['success']:
                    build = {'success': False, 'error': response['status']}
                    return build


                find_contract.ex_fare = None
                find_contract.dep_date = None
                find_contract.ret_date = None
                find_contract.flight_purchased = None
                find_contract.notes = inputs['notes']


            exercise_date_time = current_time_aware()
            find_contract.close_staged_date = exercise_date_time
            find_contract.save()
            build = {'success': True, 'search_key': search_key, 'cust_key': cust_key, 'exercise_fare': find_contract.ex_fare, 'exercise_date': exercise_date_time.strftime('%Y-%m-%d')}

            #if use_gateway:
            #    build['status'] = response['status']

            # augment cash reserve with option price
            """
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
            """
    return build
    

