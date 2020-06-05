# Changelog

## 1.2.1

* Fix for Record time processing
* New config & options for Record time processing

```
records:
    se_only: false
    all_ages_u18: false
    overall_fastest: false
```

## 1.2
01/06/2020

* Added support for iPad (Command line only)
* Added feature to manage [swimming records](Records)
* Added feature to connect directly to [Swim England](Swim_England) database to check membership details
* Added feature to connect directly to [Facebook](Facebook) to check group membership
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
