from selenium import webdriver
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json

def wait_until(browser, loc_type, id, timeout_sec):
    try:
        WebDriverWait(browser, timeout_sec).until(EC.presence_of_element_located((loc_type, id)))
    except TimeoutException:
        return False
    return True

if __name__=="__main__":
    url = 'https://customer.xfinity.com/#/billing'
    browser = webdriver.Firefox()
    browser.get(url)

    with open('logins.json') as f:
        logins = json.load(f)

    wait_until(browser, By.ID, 'user', 60)

    browser.find_element_by_id('user').send_keys(logins['Comcast']['username'])
    browser.find_element_by_id('passwd').send_keys(logins['Comcast']['password'])
    browser.find_element_by_id('sign_in').click()

    wait_until(browser, By.XPATH, "//td[text()[contains(.,'New charges')]]", 60)

    date_element = browser.find_element_by_xpath("//td[text()[contains(.,'New charges')]]")
    amt_element = browser.find_element_by_class_name(date_element.get_attribute('class').replace('name','value').replace(' ', ','))

    date_due_str = date_element.get_attribute('innerText')
    amt_due_str = amt_element.get_attribute('innerText')

    date_due = datetime.strptime(date_due_str, 'New charges due %B %d, %Y').date()
    amt_due = float(amt_due_str.replace('$',''))

    print('${} due on {}'.format(amt_due, date_due))

    browser.close()