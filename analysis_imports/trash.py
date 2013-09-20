"""
import urllib2
import urllib
data = {}
data['name'] = 'Somebody Here'
data['location'] = 'Northampton'
data['language'] = 'Python'
url_values = urllib.urlencode(data)
print url_values  # The order may differ.
url = 'http://www.example.com/example.cgi'
full_url = url + '?' + url_values
data = urllib2.urlopen(full_url)
print data
"""
import urllib2
import urllib
data = {}
data['origin_code'] = 'SFO'
data['destination_code'] = 'MAD'
data['holding_per'] = '2'
data['depart_date1'] = '2013-6-12'
data['depart_date2'] = '2013-6-13'
data['return_date1'] = '2013-6-20'
data['return_date2'] = '2013-6-22'
data['search_type'] = 'rt'
data['depart_times'] = '0'
data['return_times'] = '0'
data['nonstop'] = '0'
url_values = urllib.urlencode(data)
url = 'http://api.levelskies.com/pricing/single/'
full_url = url + '?' + url_values
data = urllib2.urlopen(full_url)
pprint(data.read())
