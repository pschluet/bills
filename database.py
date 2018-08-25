from mongoengine import *
from datetime import datetime
connect(db='bills', host='10.0.1.2', port=27017)


class BillInfo(Document):
    """
    A class that represents billing information.

    Can save itself to the MongoDB database.
    """
    amt_due = DecimalField(required=True)
    date_due = DateTimeField(required=True)
    service_name = StringField(required=True)

    def save_no_dups(self):
        """
        Save this BillInfo object to the database.

        If there is already a document with this service name and date
        update the amount with the new amount. Otherwise, make a new
        document
        """
        BillInfo.objects(service_name=self.service_name, date_due=self.date_due)\
            .update_one(set__amt_due=self.amt_due, upsert=True)


if __name__ == "__main__":
    b = BillInfo(amt_due=40.07, date_due=datetime.strptime('01/05/18', '%m/%d/%y').date(), service_name='Verizon')
    b.save_no_dups()
