from billdotcom.session import Session
from billdotcom.bill import Bill
from billdotcom.vendor import Vendor

from datetime import date
"""
sesh = Session()
sesh.login()
"""
"""
with Session() as s:
    a = Bill(
        vendorId = 'abc123',
        invoiceNumber = 'BC1234',
        invoiceDate = date(2012,10,1),
        dueDate = date(2012,11,1),
        amount = 25.0
    )
    a['id'] = s.create(a)
"""

"""
with Session() as s:
    a = Vendor(name="Test Vendor")
    a['id'] = s.create(a)
"""
with Session() as s:
	print [x['id'] for x in s.list('Vendor')]
	"""
	vendor = s.read('Vendor', id='00901POQWEGDYPO6zxqg')
	vendor['isActive'] = "1"
	s.update(vendor)
	"""
	for vendor in s.list('Vendor'):
	    vendor['isActive'] = "1"
	    s.update(vendor)


print "done"