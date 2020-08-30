# Changelog

## 1.5
30/08/2020
* GUI bug fix
* Added COVID-19 Session / Return to Swim Declaration Report.

## 1.4
20/08/2020

* Bug fix issues #14, #15
* Fix for issue #16 - LTS support
* Fix for issue #17 - Abilty to assign polo to a code of conduct
* Fix for bug #18 - not re-reading config after edit
* Fix for bug #19 - "All Reports" not showing
* Improved SE database checking
* Fix for new Facebook interface

## 1.3
26/06/2020

* Added abilty to create a list for codes of conduct not signed
* Fix for codes of conduct processing for "ignored" types
* Force re-index of items with a "Knownas" name
* Fix for record time processing
* Fix for 18-24 bug
* New [config & options](https://github.com/ColinRobbins/scm-helper/wiki/Records) for record time processing
* Added "confirmation" option to group configuration
* Checking for missing config items file on startup

```
records:
    se_only: false
    all_ages_u18: false
    overall_fastest: false
```

## 1.2
01/06/2020

* Added support for iPad (Command line only)
* Added feature to manage [swimming records](https://github.com/ColinRobbins/scm-helper/wiki/Records)
* Added feature to connect directly to [Swim England](https://github.com/ColinRobbins/scm-helper/wiki/Swim-England) database to check membership details
* Added feature to connect directly to [Facebook](https://github.com/ColinRobbins/scm-helper/wiki/Facebook) to check group membership
* Fix - config errors not showing after editing via the GUI
* Fix - Who's who not backing up correctly
* Fix - Error in reporting number of entries read
* Fix - bug in handling inactive members
* Fix - polo / synchro type now work correctly (Align with SCM Bug #6555 and #6545)

Version 1.2 requires the following to be added to your configuration file, and modified appropriately.
```
##################################################
# Swim England Correlations
##################################################
swim_england:
  base_url: "https://www.swimmingresults.org/"
  check_url: "https://www.swimmingresults.org/membershipcheck/member_details.php?myiref="
  test_id: 516115
  
##################################################
# Facebook Correlations
##################################################
facebook:
  groups:
    - https://www.facebook.com/groups/NottinghamLeander/
    
##################################################
# Selenium
# Used for Swim England and Facebook checking
##################################################
selenium:
    browser: "Chrome"
    web_driver: "C:\\Program Files (x86)\\Python37-32\\Scripts\\chromedriver.exe"

```

## 1.1
02/05/2020
* Fix for bug #6 (printing self.name rather than entity name)
* Fix for bug #7 (error processing Facebook names with spaces)
* Fix for bug #8 (Linking fails on a list with email addresses rather than members)
* Fix for bug #9 (analyse looping)
* Fix issue #10 - Fire up GUI on an Apple Mac
* Fix for bug #11 (Handling inactive member with no lastmodified attribute)
* Tidied Facebook report
* Better exception handling in GUI
* Tidied debug messages

## 1.0
23/04/2020
Initial Release
