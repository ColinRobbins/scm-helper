"""Check SE file."""

import pickle
import requests
import os.path
import selenium
from datetime import date
from pathlib import Path

from scm_helper.config import USER_AGENT, CONFIG_DIR
from scm_helper.issue import debug
from scm_helper.notify import interact_yesno, notify

from selenium.webdriver.common.keys import Keys

SE_COOKIES = "se_cookies.pkl"
WRITE_BINARY = "wb"
READ_BINARY = "rb"
WEB_DRIVER = "C:\Program Files (x86)\Python37-32\Scripts\chromedriver.exe"
SE_BASE_URL = "https://www.swimmingresults.org/"
SE_CHECK_URL = "https://www.swimmingresults.org/membershipcheck/member_details.php?myiref="
SE_TEST_ID = 516115

GENDER = {"M": "Male", "F": "Female"}

def se_check(scm, members):
    """Check members against the SE database."""
    
    home = str(Path.home())
    cookiefile = os.path.join(home, CONFIG_DIR, SE_COOKIES)
    
    browser = start_browser()
        
    if browser is None:
        return
    
    read_cookies(browser, cookiefile, SE_BASE_URL)
    
    browser.get(f"{SE_CHECK_URL}{SE_TEST_ID}")
    resp = interact_yesno("Loaded")

    write_cookies(browser, cookiefile)
         
    for member in members:
        if member.is_active is False:
            continue
        if member.asa_number is None:
            continue
            
        url = f"{SE_CHECK_URL}{member.asa_number}"
        browser.get(url)
        
        check_member(browser, member)

    browser.close()
    
def check_member(browser, member):
    """Check a member."""
    
    try:
        name = browser.find_element_by_xpath("//table[1]/tbody/tr[2]/td[2]").text
        knownas = browser.find_element_by_xpath("//table[1]/tbody/tr[2]/td[4]").text
        gender = browser.find_element_by_xpath("//table[1]/tbody/tr[3]/td[4]").text
        current = browser.find_element_by_xpath("//table[2]/tbody/tr[2]/td[4]").text
        category = browser.find_element_by_xpath("//table[2]/tbody/tr[3]/td[4]").text
        
    except selenium.common.exceptions.NoSuchElementException:
        res = f"{member.name} ({member.asa_number}) does not exist in SE database.\n"
        print (res)
        return
    
    res = ""
    if name != member.name:
        res += f"   Name: {member.name} --> {name}\n"

    if knownas and (member.knownas_only != knownas):
        res += f"   Knownas: {member.knownas_only} --> {knownas}\n"

    if member.gender and (gender != GENDER[member.gender]):
        res += f"   Gender: {member.name} --> {gender}\n"

    mycat = f"SE Category {member.asa_category}"
    if category != mycat:
        res += f"   Category: {mycat} --> {category}\n"

    if current != "Current":
        res += f"   Not current\n"

    if res:
        res = f"{member.name} ({member.asa_number}) mismatch:\n" + res
        print (res)

def start_browser():
    """Start Browser."""
    
    try:
        return selenium.webdriver.Chrome(WEB_DRIVER)
            
    except selenium.common.exceptions.WebDriverException as error:
        notify(f"Failed to open browser {WEB_DRIVER}\n{error}\n")
        return None

def read_cookies(browser, cookiefile, url):
    """Read cookies."""
    
    if os.path.isfile(cookiefile):
        browser.get(url)
        try:
            with open(cookiefile, READ_BINARY) as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    print (cookie)
                    browser.add_cookie(cookie)
                    
        except EnvironmentError as error:
            notify(f"Failed to read {cookiefile}\n{error}\n")
  
def write_cookies(browser, cookiefile):
    """Write cookies."""
    
    cookies = browser.get_cookies()
    if cookies:
        try:
            with open(cookiefile, WRITE_BINARY) as file:
                pickle.dump(cookies, file)
            
        except EnvironmentError as error:
            notify(f"Failed to write {cookiefile}\n{error}\n")

