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


class LoginManager():
    def __init__(self):
        with open('logins.json') as f:
            self._logins = json.load(f)

    def get_username(self, service_name):
        return self._logins[service_name]['username']

    def get_password(self, service_name):
        return self._logins[service_name]['password']


class ScraperUtils():
    @staticmethod
    def wait_until(browser, loc_type, id, timeout_sec):
        try:
            WebDriverWait(browser, timeout_sec).until(EC.presence_of_element_located((loc_type, id)))
        except TimeoutException:
            return False
        return True


class BillInfo():
    def __init__(self, amt_due, date_due):
        self.amtDue = amt_due
        self.dateDue = date_due


class BillDataScraper(metaclass=ABCMeta):
    _browserOptions = Options()
    _browserOptions.headless = True
    _loginManager = LoginManager()

    def __init__(self):
        self._browser = 0

    @abstractmethod
    def get_bill_info(self):
        pass


class VerizonScraper(BillDataScraper):
    pass

class ComcastScraper(BillDataScraper):

    def get_bill_info(self):
        self._browser = webdriver.Firefox(firefox_options=BillDataScraper._browserOptions)
        self._browser.get('https://customer.xfinity.com/#/billing')
        ScraperUtils.wait_until(self._browser, By.ID, 'user', 60)

        self._browser.find_element_by_id('user').send_keys(BillDataScraper._loginManager.get_username('Comcast'))
        self._browser.find_element_by_id('passwd').send_keys(BillDataScraper._loginManager.get_password('Comcast'))
        self._browser.find_element_by_id('sign_in').click()

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



if __name__=="__main__":
    executor = ThreadPoolExecutor(max_workers=4)

    with ThreadPoolExecutor(max_workers=4) as executor:
        comcast = executor.submit(ComcastScraper().get_bill_info)
        comcast2 = executor.submit(ComcastScraper().get_bill_info)

    print('${} due on {}'.format(comcast.result().amtDue, comcast.result().dateDue))