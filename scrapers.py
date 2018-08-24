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
    def __init__(self):
        with open('logins.json') as f:
            self._logins = json.load(f)

    def get_username(self, service_name):
        return self._logins[service_name]['username']

    def get_password(self, service_name):
        return self._logins[service_name]['password']


class ScraperUtils:
    @staticmethod
    def wait_until(browser, loc_type, id, timeout_sec):
        try:
            WebDriverWait(browser, timeout_sec).until(EC.presence_of_element_located((loc_type, id)))
        except TimeoutException:
            return False
        return True





class BillDataScraper(metaclass=ABCMeta):
    _browserOptions = Options()
    _browserOptions.headless = True
    _loginManager = LoginManager()

    def __init__(self):
        self._browser = 0
        self._SERVICE_NAME = ''

    @abstractmethod
    def get_bill_info(self):
        pass


class GmailScraper:
    _SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

    def __init__(self):
        self._service = self._login()

    def _login(self):
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', self._SCOPES)
            creds = tools.run_flow(flow, store)
        return build('gmail', 'v1', http=creds.authorize(Http()))

    def get_email_bodies(self, from_email='', subject='', number=1):
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
        max_size = 0
        body = ''
        for part in msg['payload']['parts']:
            if part['body']['size'] > max_size:
                body = str(base64.urlsafe_b64decode(part['body']['data']))
        return body

    def _get_email_ids_matching_query(self, query=''):
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

    def __init__(self):
        self._gmail = 0
        self._SERVICE_NAME = 'Verizon'

    def get_bill_info(self):
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

    def __init__(self):
        self._SERVICE_NAME = 'Comcast'

    def _login(self):
        ScraperUtils.wait_until(self._browser, By.ID, 'user', 60)

        self._browser.find_element_by_id('user').send_keys(BillDataScraper._loginManager.get_username('Comcast'))
        self._browser.find_element_by_id('passwd').send_keys(BillDataScraper._loginManager.get_password('Comcast'))
        self._browser.find_element_by_id('sign_in').click()

    def get_bill_info(self):
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

    def __init__(self, scrapers):
        self._scrapers = scrapers
        self._max_workers = max(len(scrapers), 4)

    def get_bill_info(self):
        bill_info_list = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            for scraper in self._scrapers:
                executor.submit(bill_info_list.append(scraper.get_bill_info()))

        return bill_info_list


if __name__ == "__main__":

    scraperExecutor = ScraperExecutor(scrapers=[ComcastScraper(), VerizonScraper()])

    bill_info = scraperExecutor.get_bill_info()

    for info in bill_info:
        print('{}: ${} due on {}'.format(info.service_name, info.amt_due, info.date_due))
