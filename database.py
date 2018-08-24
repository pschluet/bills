from mongoengine import *
from datetime import datetime
connect(db='bills', host='10.0.1.2', port=27017)

class BillInfo(Document):
    amt_due = DecimalField(required=True)
    date_due = DateTimeField(required=True)
    service_name = StringField(required=True)

if __name__ == "__main__":
    b = BillInfo(amt_due=40.02, date_due=datetime.strptime('01/02/18', '%m/%d/%y').date(), service_name='Verizon')
    b.save()