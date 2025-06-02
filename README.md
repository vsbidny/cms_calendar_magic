# cms_calendar_magic
cms_calendar_magic - a service like webex hybrid calendar connector but for Cisco Meeting Server and Exchange onprem

CMS_CALENDAR_SYNC – A Python application fully created by OpenAI, inspired by me.
Feel free to modify it as you need.

General concept:

CMS_CALENDAR_MAGIC is a service for adding CMS connection details into Outlook invitations without any plugin. It monitors the Exchange calendars of CMS users, subscribing to new meeting events by a keyword in the "location" field, for example, @cms. It adds the organizer's personal room details into the Outlook invitation. This data is obtained via the CMS REST API. It is an infrastructure service designed to run as a Windows Server service.

Tested with Exchange 2016. It should work with Exchange 2109 also, but not tested.

#It is recommended to set up the ThrottlingPolicy on Exchange ONPREM as written in the Cisco guide for the Webex hybrid calendar service:
#https://help.webex.com/en-us/article/n6cwujdb/Deployment-guide-for-Hybrid-Calendar

New-ThrottlingPolicy -Name "CalendarConnectorPolicy" -EWSMaxConcurrency unlimited -EWSMaxBurst unlimited -EWSRechargeRate unlimited -EWSCutOffBalance unlimited -EWSMaxSubscriptions 5000
Set-ThrottlingPolicyAssociation -Identity "impersonation account" -ThrottlingPolicy "CalendarConnectorPolicy"

CMS user synchronization occurs at service start/restart and then once a day according to the schedule in the settings. The service retrieves the user list from CMS, forms emails, and saves the list and last sync timestamp into \config\users.txt. Invitation templates are kept in the templates directory. The service updates the meeting on behalf of the organizer using an Impersonation Account.
Service activities are logged to separate files in the \log folder.

Structure and Launch
The main script: main_service.py (launches both user sync and calendar monitoring).


Specific environment settings are centrally set in (\config\settings.ini)         

# Yes, they are in plain text. If this does not meet your security standards, please ask the AI to change it :)

[CMS API]
base_cms_url — CMS API URL (e.g., https://cms.domain.ru:445/api/v1/)
apiuser, apipwd — credentials for CMS API.users
synctime — time of daily CMS user sync, in "HH:MM" format (e.g., 00:00)
jiddomain, sipdomain — domain for forming SIP addresses (e.g., @domain.ru).personal_room — suffix for CMS personal rooms (e.g., "space")
wb_url — external URL for guest join (e.g., https://cms.domain.ru/)

[EWS]
impers_usr, impers_pwd — email and password for the user with Exchange Impersonation role.
# read https://learn.microsoft.com/en-us/exchange/client-developer/exchange-web-services/how-to-configure-impersonation

server - Exchange server address - FQDN
magic_w — keyword for detecting CMS meetings in the calendar (e.g., @cms)
mail_domain — corporate email domain
inv_template — path to the HTML invitation template (e.g., \templates\templ1.html).

[Logging]

log.log_level — logging level (INFO, ERROR).

# Also see setting.ini.sample 


Installation:

Install Python 3.12  
Extract the archive keeping the folder structure:

\CMS_CALENDAR_MAGIC
    \logs         (the logs folder must exist)
    \config
        settings.ini   — config file for API and logging settings.
    \templates
        templ1.html 
        templ2.html 
    calendar_con.py
    main_service.py
    cms_sync.py
    meet_me.py
    requirements.txt


Installing the service on Windows using nssm.exe  
Download https://nssm.cc/download  
Open a command prompt as Administrator  
Specify the path to the Python interpreter and the main script, for example:  

nssm install CMS_CALENDAR_MAGIC "C:\Python310\python.exe" "C:\CMS_CALENDAR_MAGIC\main_service.py"

Start the service:  nssm start CMS_CALENDAR_MAGIC

Notes:
To remove the service:  nssm remove CMS_CALENDAR_MAGIC
If you encounter issues, review the contents of the \logs folder.


