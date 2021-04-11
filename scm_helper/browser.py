"""Check SE file."""

import json
import os.path
import pickle
import time
from pathlib import Path

import selenium

# pylint: disable=unused-import   #it is used!!!
from selenium.webdriver.common.keys import Keys

from scm_helper.config import (
    C_BASE_URL,
    C_BROWSER,
    C_CHECK_URL,
    C_DEBUG_LEVEL,
    C_SELENIUM,
    C_SWIM_ENGLAND,
    C_TEST_ID,
    C_WEB_DRIVER,
    CONFIG_DIR,
    EXCEPTION_SE_HIDDEN,
    EXCEPTION_SE_NAME,
    get_config,
)
from scm_helper.issue import debug
from scm_helper.notify import interact_yesno, notify

SE_COOKIES = "se_cookies.json"
FB_COOKIES = "fb_cookies.json.enc"
FILE_WRITE = "w"
FILE_READ = "r"

MEMBERS_SUFFIX = "members/"
SCROLL_PAUSE_TIME = 2

FACEBOOK = "https://www.facebook.com"

# M_XPATH = '//*[@id="groupsMemberSection_all_members"]'
# M_ENTRY = "//ul//div/div[2]/div/div[2]/div[1]"
# 05/07/2020 New Facebook GUI
# M_XPATH = '//*[@id="mount_0_0"]'
M_XPATH = '//*[contains(@id,"mount_0_0")]'
M_ENTRY = "//div/div/div[2]/div[1]/div/div/div[1]/span/span/div"
M_ELEMENTS = M_XPATH + M_ENTRY + "/a"
M_ELEMENTS2 = M_XPATH + M_ENTRY + "/span"

GENDER = {"M": "Male", "F": "Female"}


def se_check(scm, members):
    """Check members against the SE database."""

    home = str(Path.home())
    cookiefile = os.path.join(home, CONFIG_DIR, SE_COOKIES)

    base_url = get_config(scm, C_SWIM_ENGLAND, C_BASE_URL)
    if base_url is False:
        notify("Swim England config missing\n")
        return None

    notify(f"Opening browser for {base_url}...\n")

    browser = start_browser(scm)

    if browser is None:
        return None

    read_cookies(browser, cookiefile, base_url, None)

    check_url = get_config(scm, C_SWIM_ENGLAND, C_CHECK_URL)
    test_id_url = get_config(scm, C_SWIM_ENGLAND, C_TEST_ID)

    browser.get(f"{check_url}{test_id_url}")
    try:
        browser.find_element_by_xpath("//table[1]/tbody/tr[2]/td[2]")

    except selenium.common.exceptions.NoSuchElementException:
        msg = """Please solve the 'I am not a robot', and then press enter here.
If you cannot solve the capture try deleting the file 'se_cookies.json'
in the config directory.
"""
        interact_yesno(msg)
        write_cookies(browser, cookiefile, None)

    res = ""
    for member in members:
        if member.is_active is False:
            continue
        if member.asa_number is None:
            continue

        url = f"{check_url}{member.asa_number}"
        browser.get(url)

        res += check_member(browser, member)

    browser.close()

    return res


def fb_read_url(scm, url):
    """Read Facebook Group members."""

    users = []

    home = str(Path.home())
    cookiefile = os.path.join(home, CONFIG_DIR, FB_COOKIES)

    notify(f"Opening browser for {url}...\n")

    url += MEMBERS_SUFFIX

    browser = start_browser(scm)

    if browser is None:
        return None

    read_cookies(browser, cookiefile, FACEBOOK, scm)

    browser.get(url)
    try:
        browser.find_element_by_xpath(M_XPATH)
    except selenium.common.exceptions.NoSuchElementException:
        interact_yesno("Please logon to Facebook and then press enter here.")
        write_cookies(browser, cookiefile, scm)
        browser.get(url)

    debug_config = scm.config(C_DEBUG_LEVEL)
    if debug_config > 1:
        interact_yesno(
            "Navigate to members page (if not there) - then Click to Continue"
        )

    scroll(browser)

    count = 0
    for path in [M_ELEMENTS, M_ELEMENTS2]:
        elements = browser.find_elements_by_xpath(path)
        for element in elements:
            if element.text not in users:
                count += 1
                users.append(element.text)

    notify(f"Read {count} names from {url}\n")
    browser.close()

    return users


def scroll(browser):
    """Scroll to end of page."""

    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    notify("Scrolling")

    while True:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)
        notify(".")

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            notify("Done\n")
            return
        last_height = new_height


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
        if member.print_exception(EXCEPTION_SE_HIDDEN) is False:
            debug(f"SE Exception ignored: {member.name}", 7)
            return ""

        res = f"\n{member.name} ({member.asa_number}) does not exist in SE database.\n"
        return res

    res = ""

    if member.print_exception(EXCEPTION_SE_NAME) is True:
        if name.lower() != member.name.lower():
            res += f"   Name: SCM-> {member.name}, SE-> {name}\n"

        if knownas and (member.knownas_only != knownas):
            firstname = name.split(" ")
            if knownas != firstname[0]:  # in SE they are the same if no knownas
                res += f"   Knownas: SCM-> {member.knownas_only}, SE-> {knownas}\n"

    if member.gender and (gender != GENDER[member.gender]):
        res += f"   Gender: SCM-> {member.name}, SE-> {gender}\n"

    mycat = f"SE Category {member.asa_category}"
    if category != mycat:
        res += f"   Category: SCM-> {mycat}, SE-> {category}\n"

    if current != "Current":
        res += "   Not current\n"

    if res:
        res = f"\n{member.name} ({member.asa_number}) mismatch:\n" + res

    return res


def start_browser(scm):
    """Start Browser."""

    web_driver = get_config(scm, C_SELENIUM, C_WEB_DRIVER)
    client = get_config(scm, C_SELENIUM, C_BROWSER)

    if client is False:
        notify("Selenium config missing\n")
        return None

    browser = getattr(selenium.webdriver, client)

    try:
        return browser(web_driver)

    except selenium.common.exceptions.WebDriverException as error:
        notify(f"Failed to open {client} browser with: {web_driver}\n{error}\n")
        return None


def read_cookies(browser, cookiefile, url, scm):
    """Read cookies."""

    if os.path.isfile(cookiefile):
        browser.get(url)

        if scm:
            data = scm.crypto.decrypt_file(cookiefile)
            if data:
                cookies = pickle.loads(data)
        else:
            try:
                with open(cookiefile, FILE_READ) as file:
                    data = file.read()
                    cookies = json.loads(data)

            except EnvironmentError as error:
                notify(f"Failed to read {cookiefile}\n{error}\n")

        for cookie in cookies:
            if "expiry" in cookie:
                del cookie["expiry"]
            browser.add_cookie(cookie)


def write_cookies(browser, cookiefile, scm):
    """Write cookies."""

    cookies = browser.get_cookies()

    if cookies:
        if scm:
            data = pickle.dumps(cookies)
            scm.crypto.encrypt_file(cookiefile, data)
            return

        try:
            with open(cookiefile, FILE_WRITE) as file:
                opt = json.dumps(cookies)
                file.write(opt)

        except EnvironmentError as error:
            notify(f"Failed to write {cookiefile}\n{error}\n")
