from abc import ABCMeta, abstractmethod
from events import Observer, EventTypes
from mongoengine import *
from datetime import datetime
from mongoengine.document import TopLevelDocumentMetaclass
connect(db='bills', host='10.0.1.2', port=27017)


class Meta(ABCMeta, TopLevelDocumentMetaclass):
    """
    Needed to support double inheritance with base classes having different metaclasses (i.e.
    BillInfo inheriting from Document and DatabaseItem)
    """
    pass


class DatabaseItem(metaclass=ABCMeta):
    """
    Abstract class for all database Document extensions
    """
    @abstractmethod
    def save_no_dups(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass


class BillInfo(Document, DatabaseItem, metaclass=Meta):
    """
    A class that represents billing information.

    Can save itself to the MongoDB database.
    """
    amt_due = DecimalField(required=True)
    date_due = DateTimeField(required=True)
    service_name = StringField(required=True)

    def to_dict(self):
        """
        Convert object to dictionary for ease of loading into pandas for plotting

        :return: a dictionary that represents this object
        """
        return {
            "amt_due": self.amt_due,
            "date_due": self.date_due,
            "service_name": self.service_name
        }

    def save_no_dups(self):
        """
        Save this BillInfo object to the database.

        If there is already a document with this service name and date
        update the amount with the new amount. Otherwise, make a new
        document
        """
        BillInfo.objects(service_name=self.service_name, date_due=self.date_due)\
            .update_one(set__amt_due=self.amt_due, upsert=True)


class ExecutionStatus(Document, DatabaseItem, metaclass=Meta):
    """
    A class that represents the success or failure of a scraping operation.

    Can save itself to the MongoDB database.
    """
    service_name = StringField(required=True)
    success = BooleanField(required=True)
    exec_time = DateTimeField(required=True)
    error_message = StringField()

    def to_dict(self):
        """
        Convert object to dictionary for ease of loading into pandas for plotting

        :return: a dictionary that represents this object
        """
        return {
            "service_name": self.service_name,
            "success": self.success,
            "exec_time": self.exec_time,
            "error_message": self.error_message
        }

    def save_no_dups(self):
        """
        Save this ExecutionStatus object to the database.

        If there is already a document with this service name and execution
        time, update the success and error message with the new values. Otherwise,
        create a new document.
        """
        ExecutionStatus.objects(service_name=self.service_name, exec_time=self.exec_time)\
            .update_one(set__success=self.success, set__error_message=self.error_message, upsert=True)


class ScrapeResultSaveHandler(Observer):
    """
    Handles saving scraping results to the database
    """
    def __init__(self):
        Observer.__init__(self)

    def handle_scraping_result(self, data):
        """
        Handles events of type EventTypes.SCRAPING_EXECUTION_FINISHED

        :param data: ScrapingExecutionFinishedEventData event data object
        """
        data.exec_status.save_no_dups()
        if data.exec_status.success:
            data.billing_info.save_no_dups()
            print('{}: ${} due on {}'.format(data.billing_info.service_name, data.billing_info.amt_due,
                                             data.billing_info.date_due))


if __name__ == "__main__":
    b = BillInfo(amt_due=40.07, date_due=datetime.strptime('01/05/18', '%m/%d/%y').date(), service_name='Verizon')
    b.save_no_dups()
