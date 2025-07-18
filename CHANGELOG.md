# Changelog

## 1.10.1
18/7/2025
* Code quality changes

## 1.10.0
18/07/2025
* SCM API breaking change: Boolean type (Issue #59)
* Enhancement: Issue 50 - multiple types in a Group
* Enhancement: Issue 54 - multiple groups or types in search for creating a list.
* Latest PyLint fixes.
* Removed leagacy features no longer needed (Covid and fix index)

## 1.9.5
01/3/2025
* Fixed errors in coaces fixit

## 1.9.4
29/03/2024
* Added more options to exclude swimmer not entitled to records

## 1.9.3
11/10/2023
* Fixed Selenium Driver download (Issue #57)

## 1.9.2
15/07/2022
* Added check for login for select groups

## 1.9.1
16/03/2022
* Fix date format in records.

## 1.9
* Add support for filters in records

## 1.8.3
* Fix SE Category Matching

## 1.8.2
* Fix date format from excel

## 1.8.2
* Fix error message when using wrong Chrome driver

## 1.8.1
03/11/2021
* Fix recording procesing [bug](https://github.com/ColinRobbins/scm-helper/issues/45)

## 1.8
31/10/2021
* Global edit of SE Category to [new names](https://github.com/ColinRobbins/scm-helper/issues/44)
* Check SE Category are valid

## 1.7.7
22/10/2021
* Pylint tidying
* Fix for issue [43](https://github.com/ColinRobbins/scm-helper/issues/43)

## 1.7.6
25/09/2021
* Added support for "Master" type.

## 1.7.5
18/08/2021
* Bug fix - records handling failing after update 1.5
* Added Facebook XPATH as a config option

## 1.7.4
25/07/2021
* Bug fix - deal with null session data in fixit.
* Bug Fix - Facebook changed XPath

## 1.7.3
06/60/2021
* Fix issue [4](https://github.com/ColinRobbins/scm-helper/issues/4)

## 1.7.2
* Added option to exclude session from count of sessions per swimmer
* Print last seen date on Covid Report

## 1.7.1
* Updated example config
* Updated Facebook page analysis
* Fix bug preventing config reloading correctly after an edit

## 1.7
10/04/2021
* COVID list generation bug fix
* Create issue if max swimmers per session exceeded - configurable per-group

## 1.6
07/04/2021
* Fix EOY date issue
* Add Date to Code of Conduct check
* Add report: grid of swimmers per session

## 1.5.1
28/09/2020
* Create issue if max swimmers per session exceeded

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
