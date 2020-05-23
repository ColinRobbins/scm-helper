"""Check SE file."""

import requests

from scm_helper.config import USER_AGENT
from scm_helper.issue import debug
from scm_helper.notify import notify


def se_check(member):
    """Check a member against the SE database."""
    
    if member.asa_number is None:
        return None
        

    user_agent = USER_AGENT.replace("###CLUB_NAME###", "TEST")
    
    url = f"https://www.swimmingresults.org/membershipcheck/member_details.php?myiref={member.asa_number}"

    headers = {
        "User-Agent": user_agent,
    }

    debug(f"URL:\n{url}", 9)
    debug(f"Headers:\n{headers}", 8)

    response = requests.get(url, headers=headers)
    if response.ok:
        print (f"HERE:\n{response.text}")

    notify(f"\nErroring getting data from {url}, \n")
    notify(response.reason)
    notify("\n")
    return None
