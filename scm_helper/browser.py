"""Check SE file."""

import json
import requests
import os.path
import selenium
from datetime import date
from pathlib import Path

from scm_helper.config import USER_AGENT, CONFIG_DIR, C_SELENIUM, C_BROWSER,  C_WEB_DRIVER,  C_SWIM_ENGLAND,  C_BASE_URL,  C_CHECK_URL,  C_TEST_ID, get_config
from scm_helper.issue import debug
from scm_helper.notify import interact_yesno, notify

from selenium.webdriver.common.keys import Keys

SE_COOKIES = "se_cookies.json"
FILE_WRITE = "w"
FILE_READ = "r"

GENDER = {"M": "Male", "F": "Female"}

def se_check(scm, members):
    """Check members against the SE database."""
    
    home = str(Path.home())
    cookiefile = os.path.join(home, CONFIG_DIR, SE_COOKIES)
    
    browser = start_browser(scm)
        
    if browser is None:
        return None
    
    base_url = get_config(scm, C_SWIM_ENGLAND, C_BASE_URL)
    if base_url is False:
        notify ("Swim England config missing\n")
        return None

    read_cookies(browser, cookiefile, base_url)
    
    check_url = get_config(scm, C_SWIM_ENGLAND, C_CHECK_URL)
    test_id_url = get_config(scm, C_SWIM_ENGLAND, C_TEST_ID)

    browser.get(f"{check_url}{test_id_url}")
    try:
        name = browser.find_element_by_xpath("//table[1]/tbody/tr[2]/td[2]").text

    except selenium.common.exceptions.NoSuchElementException:
        resp = interact_yesno("Please solve the 'I am not a robot', and then press enter here.")

    write_cookies(browser, cookiefile)
         
    res = ""
    for member in members:
        if member.is_active is False:
            continue
        if member.asa_number is None:
            continue
            
        url = f"{check_url}{member.asa_number}"
        browser.get(url)
        
        res += check_member(browser, member)

    write_cookies(browser, cookiefile)
    browser.close()
    
    return res
    
def check_member(browser, member):
    """Check a member."""
    
    notify(f"Checking {member.name}...\n")
    
    try:
        name = browser.find_element_by_xpath("//table[1]/tbody/tr[2]/td[2]").text
        knownas = browser.find_element_by_xpath("//table[1]/tbody/tr[2]/td[4]").text
        gender = browser.find_element_by_xpath("//table[1]/tbody/tr[3]/td[4]").text
        current = browser.find_element_by_xpath("//table[2]/tbody/tr[2]/td[4]").text
        category = browser.find_element_by_xpath("//table[2]/tbody/tr[3]/td[4]").text
        
    except selenium.common.exceptions.NoSuchElementException:
        res = f"{member.name} ({member.asa_number}) does not exist in SE database.\n"
        return res
    
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
    
    return res

def start_browser(scm):
    """Start Browser."""

    web_driver = get_config(scm, C_SELENIUM, C_WEB_DRIVER)
    client = get_config(scm, C_SELENIUM, C_BROWSER)

    if client is False:
        notify ("Selenium config missing\n")
        return None

    browser = getattr(selenium.webdriver,client)

    try:
        return browser(web_driver)
            
    except selenium.common.exceptions.WebDriverException as error:
        notify(f"Failed to open {client} browser with: {web_driver}\n{error}\n")
        return None

def read_cookies(browser, cookiefile, url):
    """Read cookies."""
    
    if os.path.isfile(cookiefile):
        browser.get(url)
        try:
            with open(cookiefile, FILE_READ) as file:
                data = file.read()
                cookies = json.loads(data)
                for cookie in cookies:
                    browser.add_cookie(cookie)
                    
        except EnvironmentError as error:
            notify(f"Failed to read {cookiefile}\n{error}\n")
  
def write_cookies(browser, cookiefile):
    """Write cookies."""
    
    cookies = browser.get_cookies()
    if cookies:
        try:
            with open(cookiefile, FILE_WRITE) as file:
                opt = json.dumps(cookies)
                file.write(opt)
            
        except EnvironmentError as error:
            notify(f"Failed to write {cookiefile}\n{error}\n")

