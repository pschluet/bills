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


class BillInfo:
    def __init__(self, amt_due, date_due):
        self.amtDue = amt_due
        self.dateDue = date_due


class BillDataScraper(metaclass=ABCMeta):
    _browserOptions = Options()
    _browserOptions.headless = False
    _loginManager = LoginManager()

    def __init__(self):
        self._browser = 0

    @abstractmethod
    def get_bill_info(self):
        pass

class GmailScraper:
    _SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

    def __init__(self):
        self._service = self._login()
        pass

    def _login(self):
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', self._SCOPES)
            creds = tools.run_flow(flow, store)
        return build('gmail', 'v1', http=creds.authorize(Http()))

    def get_emails(self, from_email='', subject='', number=1):
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
                out.append(result)
        return out

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

    def _login(self):
        ScraperUtils.wait_until(self._browser, By.ID, 'IDToken1', 60)

        self._browser.find_element_by_id('IDToken1').send_keys(BillDataScraper._loginManager.get_username('Verizon'))
        self._browser.find_element_by_id('IDToken2').send_keys(BillDataScraper._loginManager.get_password('Verizon'))
        self._browser.find_element_by_id('login-submit').click()

    def get_bill_info(self):
        self._browser = webdriver.Firefox(firefox_options=BillDataScraper._browserOptions)
        self._browser.get('https://myvpostpay.verizonwireless.com/ui/bill/ao/viewbill#!/')

        self._login()

        bp = 1


class ComcastScraper(BillDataScraper):

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

        return BillInfo(amt_due=amt_due, date_due=date_due)


if __name__ == "__main__":
    gs = GmailScraper()
    mail = gs.get_emails(from_email='VZWMail@ecrmemail.verizonwireless.com', subject='"Your online bill is available"')
    with open('out.txt','w') as f:
        json.dump(mail,f,indent=4)
    # executor = ThreadPoolExecutor(max_workers=4)
    #
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     comcast = executor.submit(ComcastScraper().get_bill_info)
    #     verizon = executor.submit(VerizonScraper().get_bill_info)
    #
    # print('${} due on {}'.format(comcast.result().amtDue, comcast.result().dateDue))