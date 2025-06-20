# CMS_CALENDAR_MAGIC

**CMS_CALENDAR_MAGIC** – a Python application entirely created by OpenAI (with some persuasion and dramatic flair from me). I didn’t manually write or edit a single line of code.

## General Description

**CMS_CALENDAR_MAGIC** is a service for adding Cisco Meeting Server (CMS) connection details to Outlook invitations — without any plugins. It monitors the Exchange calendars of CMS users, subscribing to new events with a specific keyword in the "Location" field (e.g., `@cms`), and inserts personal room connection info of the organizer into the Outlook invite. These details are fetched via the CMS REST API. This is an infrastructure-level service designed to run as a Windows Server background service.

Tested with **Exchange 2016**. Expected to work with Exchange 2019, though not tested.

### Set up throttling policy in Exchange:

```powershell
New-ThrottlingPolicy -Name "CalendarConnectorPolicy" -EWSMaxConcurrency unlimited -EWSMaxBurst unlimited -EWSRechargeRate unlimited -EWSCutOffBalance unlimited -EWSMaxSubscriptions 5000
Set-ThrottlingPolicyAssociation -Identity "impersonation account" -ThrottlingPolicy "CalendarConnectorPolicy"
```

User sync from **CMS** occurs on service **startup/restart**, and then **once daily** at a time specified in `settings.ini`.  
The service fetches the CMS user list, builds their email addresses, and saves them (plus timestamp) to `\config\users.txt`.  
Email invite templates are stored in the `templates` folder.  
It updates meetings on behalf of the organizer using impersonation.  
Actions are logged in the `\log` folder.

---

## Structure and Launch

Main script: `main_service.py`  
Environment variables and config: `\config\settings.ini`  
**Note**: Integration passwords are stored in **plain text**. You can modify this if desired.

---

## Installation

### 1. Install Python 3

```powershell
$pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
$installerPath = "$env:TEMP\python-installer.exe"
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath
Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
$pythonPath = "C:\Program Files\Python312"
$pythonScriptsPath = "$pythonPath\Scripts"
[System.Environment]::SetEnvironmentVariable("PATH", "$($env:PATH);$pythonPath;$pythonScriptsPath", "Machine")
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
python --version
```

### 2. Extract Archive & Preserve Structure

```
CMS_Calendar_Magic/
├── logs/
├── config/
│   └── settings.ini
├── templates/
│   ├── templ1.html
│   └── templ2.html
├── calendar_con.py
├── main_service.py
├── cms_MAGIC.py
├── meet_me.py
└── requirements.txt
```

### 3. Edit `settings.ini`

#### [CMS API]
- `base_cms_url`: e.g., `https://cms.domain.ru:445/api/v1/`
- `apiuser`, `apipwd`: CMS API credentials
- `MAGICtime`: daily sync time in "HH:MM" format (e.g., `00:00`)
- `jiddomain`: CMS user domain
- `sipdomain`: SIP address domain (e.g., `@domain.ru`)
- `personal_room`: suffix for personal rooms (e.g., `space`)
- `wb_url`: external guest join URL (e.g., `https://cms.domain.ru/`)

#### [EWS]
- `impers_usr`, `impers_pwd`: impersonation account credentials  
  Read more: https://learn.microsoft.com/en-us/exchange/client-developer/exchange-web-services/how-to-configure-impersonation
- `server`: Exchange FQDN
- `magic_w`: keyword to detect CMS meetings (e.g., `@cms`)
- `mail_domain`: corporate email domain
- `inv_template`: path to HTML invite template (e.g., `\templates\templ1.html`)

#### [Logging]
- `log_level`: INFO or ERROR

> See also: `settings.ini.sample`

---

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Install as Windows Service with nssm.exe

**5.1 Download and extract `nssm.exe`:**

```powershell
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "C:\Users\Public\Downloads\nssm-2.24.zip"
Expand-Archive -Path "C:\Users\Public\Downloads\nssm-2.24.zip" -DestinationPath "C:\nssm" -Force
```

**5.2 Install and start service:**

```powershell
cmd /c C:\nssm\nssm-2.24\win64\nssm install CMS_Calendar_Magic "C:\Program Files\Python312\python.exe" "C:\CMS_Calendar_Magic\main_service.py"
cmd /c C:\nssm\nssm-2.24\win64\nssm start CMS_Calendar_Magic
```

> **To remove the service:**  
> `nssm remove CMS_Calendar_Magic`  
> **Troubleshooting?** Check the `\logs` folder.

---

**Author**: Vlad Bidny (@vvladus33)  
**Editor**: Rais Khasanov (@gambit295)  
**Last updated**: June 17, 2025