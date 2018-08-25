from selenium import webdriver
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
import json
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import base64

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient import errors

from database import BillInfo

from bs4 import BeautifulSoup
import re


class LoginManager:
    """
    Handles parsing the logins.json file and delivers usernames and
    passwords to consumers
    """
    def __init__(self):
        """Constructor: loads the logins.json file"""
        with open('logins.json') as f:
            self._logins = json.load(f)

    def get_username(self, service_name):
        """
        :param service_name: the service (i.e. 'Comcast', 'Verizon', etc.)
        :return: a string username
        """
        return self._logins[service_name]['username']

    def get_password(self, service_name):
        """
        :param service_name: the service (i.e. 'Comcast', 'Verizon', etc.)
        :return: a string password
        """
        return self._logins[service_name]['password']


class ScraperUtils:
    """Helper class to wait until a new page has loaded for scraping"""
    @staticmethod
    def wait_until(browser, loc_type, id, timeout_sec):
        """
        Wait until a particular DOM element exists on the page

        :param browser: selenium WebDriver
        :param loc_type: By type; locator strategy; the type of thing to wait for
        :param id: the text defining the item to wait for
        :param timeout_sec: time to wait in seconds
        :return: True if the item was found within timeout, else False
        """
        try:
            WebDriverWait(browser, timeout_sec).until(EC.presence_of_element_located((loc_type, id)))
        except TimeoutException:
            return False
        return True


class BillDataScraper(metaclass=ABCMeta):
    """
    Abstract base class for all bill data scrapers
    """
    _browserOptions = Options()
    _browserOptions.headless = True
    _loginManager = LoginManager()

    def __init__(self):
        self._browser = 0
        self._SERVICE_NAME = ''

    @abstractmethod
    def get_bill_info(self):
        """
        Scrape the bill information
        :return: a BillInfo object representing information about bills
        """
        pass


class GmailScraper:
    """
    A class to handle scraping Gmail messages
    """
    _SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

    def __init__(self):
        self._service = self._login()

    def _login(self):
        """
        Authenticate with the Gmail service

        :return: A Resource object with methods for interacting with the service
        """
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', self._SCOPES)
            creds = tools.run_flow(flow, store)
        return build('gmail', 'v1', http=creds.authorize(Http()))

    def get_email_bodies(self, from_email='', subject='', number=1):
        """
        Get the bodies of e-mails that match the provided search filters

        :param from_email: the e-mail address that sent the e-mail
        :param subject: the subject of the e-mail
        :param number: the number of e-mails to retrieve
        :return: a list of strings (bodies of e-mails)
        """
        out = []
        query = ''
        if from_email:
            query += 'from:' + from_email + ' '
        if subject:
            query += 'subject:' + subject + ' '

        ids = self._get_email_ids_matching_query(query)
        for info in ids[:number]:
            result = self._service.users().messages().get(userId='me', id=info['id'], format='full').execute()
            if result:
                out.append(self._get_largest_payload_part(result))
        return out

    def _get_largest_payload_part(self, msg):
        """
        Search through the e-mail payload and pick out the largest one. Assume that's the body.

        :param msg: A gmail message
        :return: A string; the gmail message body
        """
        max_size = 0
        body = ''
        for part in msg['payload']['parts']:
            if part['body']['size'] > max_size:
                body = str(base64.urlsafe_b64decode(part['body']['data']))
        return body

    def _get_email_ids_matching_query(self, query=''):
        """
        Get a list of e-mail IDs and thread IDs that match the search query

        :param query: query string; same format that would be used in Gmail search field
        :return: a list of dicts; each dict has the keys: 'id', 'threadId'
        """
        try:
            response = self._service.users().messages().list(userId='me', q=query).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = self._service.users().messages().list(userId='me', q=query,
                                                           pageToken=page_token).execute()
                messages.extend(response['messages'])

            return messages
        except (errors.HttpError) as error:
            print('An error occurred: {}'.format(error))


class VerizonScraper(BillDataScraper):
    """
    Class to scrape Verizon e-mails for billing information
    """

    def __init__(self):
        self._gmail = 0
        self._SERVICE_NAME = 'Verizon'

    def get_bill_info(self):
        """
        Scrape the Verizon e-mails for billing information

        :return: a BillInfo object representing information about bills
        """
        self._gmail = GmailScraper()
        email_html = self._gmail.get_email_bodies(from_email='VZWMail@ecrmemail.verizonwireless.com',
                                                         subject='"Your online bill is available"',
                                                         number=1)
        soup = BeautifulSoup(email_html[0], 'html.parser')

        amt_due_str = soup.find('div', text=re.compile('\$\d+\.\d{2}')).text
        date_due_str = soup.find('div', text=re.compile('\d{2}/\d{2}/\d{2}')).text

        date_due = datetime.strptime(date_due_str, '%m/%d/%y').date()
        amt_due = float(amt_due_str.replace('$', ''))

        return BillInfo(amt_due=amt_due, date_due=date_due, service_name=self._SERVICE_NAME)


class ComcastScraper(BillDataScraper):
    """
    Class to scrape the Comcast website for billing information
    """

    def __init__(self):
        self._SERVICE_NAME = 'Comcast'

    def _login(self):
        """
        Login to the Comcast website
        """
        ScraperUtils.wait_until(self._browser, By.ID, 'user', 60)

        self._browser.find_element_by_id('user').send_keys(BillDataScraper._loginManager.get_username('Comcast'))
        self._browser.find_element_by_id('passwd').send_keys(BillDataScraper._loginManager.get_password('Comcast'))
        self._browser.find_element_by_id('sign_in').click()

    def get_bill_info(self):
        """
        Scrape the Comcast website for billing information

        :return: a BillInfo object representing information about bills
        """
        self._browser = webdriver.Firefox(firefox_options=BillDataScraper._browserOptions)
        self._browser.get('https://customer.xfinity.com/#/billing')

        self._login()

        ScraperUtils.wait_until(self._browser, By.XPATH, "//td[text()[contains(.,'New charges')]]", 60)

        date_element = self._browser.find_element_by_xpath("//td[text()[contains(.,'New charges')]]")
        amt_element = self._browser.find_element_by_class_name(
            date_element.get_attribute('class').replace('name', 'value').replace(' ', ','))

        date_due_str = date_element.get_attribute('innerText')
        amt_due_str = amt_element.get_attribute('innerText')

        date_due = datetime.strptime(date_due_str, 'New charges due %B %d, %Y').date()
        amt_due = float(amt_due_str.replace('$', ''))

        self._browser.close()

        return BillInfo(amt_due=amt_due, date_due=date_due, service_name=self._SERVICE_NAME)


class ScraperExecutor:
    """
    A class for executing scraping operations in parallel
    """

    def __init__(self, scrapers):
        """
        Constructor

        :param scrapers: A list of BillDataScraper subclass instances
        """
        self._scrapers = scrapers
        self._max_workers = max(len(scrapers), 4)

    def get_bill_info(self):
        """
        Execute the scraping operations in a multi-threaded fashion (in parallel)

        :return: a list of BillInfo objects
        """
        bill_info_list = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            for scraper in self._scrapers:
                executor.submit(bill_info_list.append(scraper.get_bill_info()))

        return bill_info_list


if __name__ == "__main__":

    scraperExecutor = ScraperExecutor(scrapers=[ComcastScraper(), VerizonScraper()])

    bill_info = scraperExecutor.get_bill_info()

    for info in bill_info:
        info.save_no_dups()
        print('{}: ${} due on {}'.format(info.service_name, info.amt_due, info.date_due))
