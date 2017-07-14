<div align="center">

  <br />

  <a align="center" href=""> <img height="300" width="500" src="https://user-images.githubusercontent.com/18141485/28209680-78d39b40-688b-11e7-983b-be5b76c897a2.gif" alt="A Feedback-driven GUI master/actuator orchestration framework for the OpenC2 language, written in Python. Works in remote security management. Loves to travel. Enjoys meeting new people. Good listener."/>

  <h1 align="center">Reactor Master</h1>
  
  <strong>A Feedback-driven GUI master / actuator orchestration framework for the OpenC2 language, written in Python</strong>
  
</div>

<br />

<div align="center">
  <a href=""> <img src="https://img.shields.io/badge/python-2.7-blue.svg?style=flat-square" alt="python versions" />
  </a>
  <!-- Stage -->
  <a href=""> <img src="https://img.shields.io/badge/stage-dev-yellow.svg?style=flat-square" alt="build stage" />
  </a>
</div>    

---

## Foreword

This project is proof of concept code to show how OpenC2 can be deployed on geographically disparate networks. Please report bugs via git issues, pull requests are welcome.


## History

This project is built on top of OrchID's code base: 

[OrchID](https://github.com/OpenC2-org/OrchID) is an OpenC2 proxy built in [Django](https://www.djangoproject.com/) 1.10.2. OrchID aims to provide a simple, modular API to begin accepting OpenC2 commands and converting them into Python actions.

OpenC2 OrchID was built by [Adam Bradbury](#creator) (Zepko Architect), so is used extensively in Zepko's response architecture. This document explains the usage for the onboarded profiles for this version of OrchID, for general documentation on how OrchID functions you should refer to the official [repository](https://github.com/OpenC2-org/OrchID).


## Purpose

This code base provides a way to administrate multiple [ReactorRelay](https://github.com/OpenC2-org/ReactorRelay) deployments. It provides an OpenC2 API to send commands to downstream relays, as well as a way for analyst to manually send commands to capable actuators deployed on client's sites that wouldn't be accessible directly from the internet.


## Installation _(CentOS 7.3)_

### 1. Install dependencies 

  ```shell
  yum install -y git wget python-pip python-devel gcc mariadb mariadb-server mariadb-devel MySQL-python libffi-devel
  ```

### 2. Configure the database 

  ```shell
  systemctl status mariadb.service
  systemctl start mariadb.service
  systemctl enable mariadb.service
  
  mysql_secure_installation
  ```

  ```shell
  
  NOTE: RUNNING ALL PARTS OF THIS SCRIPT IS RECOMMENDED FOR ALL MariaDB
        SERVERS IN PRODUCTION USE!  PLEASE READ EACH STEP CAREFULLY!
  
  In order to log into MariaDB to secure it, we'll need the current
  password for the root user.  If you've just installed MariaDB, and
  you haven't set the root password yet, the password will be blank,
  so you should just press enter here.
  
  Enter current password for root (enter for none):
  ```
> Press enter for first time installs

  ```shell
  Change the root password? [Y/n]
  ```
> It's recommended that you set a strong password for the root account
> By default the password for Reactor is `correcthorsebatterystaple`

  ```shell
  Remove anonymous users? [Y/n]
  ```
> It is recommended that all anonymous remote logins be disabled

  ```shell
  Disallow root login remotely? [Y/n]
  ```
> It is recommended that the root account only login from `localhost`

  ```shell
  Remove test database and access to it? [Y/n]
  ```
> It is recommended that the test database is removed for security

  ```shell
  Reload privilege tables now? [Y/n]
  ```
> Choose Y to apply the new settings

  ```shell
  Cleaning up...
  
  All done!  If you've completed all of the above steps, your MariaDB
  installation should now be secure.
  
  Thanks for using MariaDB!
  ```

### 3. Configure the firewall _(`firewall-cmd` on CentOS 7.3)_

> Reactor Master uses port `9000` by default - set by `OPENC2_RESPONSE_URL` - which can be changed in `main/settings.py`

  ```python
  35  # OpenC2 Response URL 
  36  OPENC2_RESPONSE_URL = 'http://0.0.0.0:9000/openc2/'
  ```

> Either create port rules for the necessary ports required by Reactor, or disable the firewall altogether *(not recommended)*

##### _(Optional)_ Disable firewall

  ```shell
  systemctl stop firewall-cmd
  systemctl disable firewall-cmd
  ```

##### Enable firewall

  ```shell
  firewall-cmd --state
  running
  ```

  ```
  systemctl status firewall-cmd
  systemctl start firewall-cmd
  systemctl enable firewall-cmd
  ```

##### Create firewall port rules

  ```shell
  firewall-cmd --add-port=9000/tcp --zone=public --permanent   # ReactorMaster
  
  firewall-cmd --reload
  ```

##### Create cron task for job polling

  ```shell
  echo "*/1 * * * * root /usr/bin/wget --spider -q http://:9000/cron/launch/ > /dev/null" >> /etc/crontab
  ```

### 4. Configure the project environment(s)  

  ```shell
  git clone https://User:Token@github.com/User/ReactorMaster.git
  ```

> OR...

  ```shell
  git clone https://github.com/User/ReactorMaster.git
  
  Enter username and password...
  ```

##### Familiarise yourself with the code base. If you're familiar with Django projects then this will be very familiar.
  
  ```shell
  cd ReactorMaster && ls
  
  LICENSE  main  manage.py  reactor_master  README.md  requirements.txt  samples  static
  ```

##### Upgrade pip
  
  ```shell
  pip install --upgrade pip
  ```

##### Install *virtualenv* package

  ```shell
  pip install virtualenv
  ```

##### Create a new virtual environment

> If you are testing both ReactorRelay and ReactorMaster on the same system, you can use one virtual environment for both

```shell
virtualenv env/ -p python --prompt="[ReactorMaster]"
```

##### Activate virtual environment

```shell
source env/bin/activate
```

##### Deactivate virtual environment

```shell
deactivate
```

### 5. Set up the application (must be in virtual environment) 

##### Install dependencies

```shell
pip install -r requirements.txt
```

##### Configure Django

> For database migrations, you may need to first create the schema specified on line 90 in `main/settings.py`

```shell
mysql -uroot -p   # provide password when prompted
```

```mysql
MariaDB [(none)]> show schemas;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
+--------------------+
3 rows in set (0.00 sec)

create schema reactor_master;
Query OK, 1 row affected (0.00 sec)

MariaDB [(none)]> show schemas;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| reactor_master     |
+--------------------+
4 rows in set (0.00 sec)

exit
Bye
```

##### Update database to latest schema

```shell
python manage.py migrate   # configures database according to models and previous migrations

Operations to perform:
  Apply all migrations: admin, auth, contenttypes, reactor_master, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying reactor_master.0001_initial... OK
  Applying sessions.0001_initial... OK
```

##### Load the starting data into the database

```shell
python manage.py loaddata reactor_master/fixtures/initial_data.json
```

##### Create a superuser to manage the project

```shell
python manage.py createsuperuser
```

##### Launch the server

```shell
python manage.py runserver 0.0.0.0:9000   # master

Performing system checks...

2017-07-10 20:40:42,252 INFO Registered response name with signature {'action': 'response', 'target': {'type': 'openc2:Data'}}
2017-07-10 20:40:42,410 INFO Initialising master
2017-07-10 20:40:42,410 INFO Loading profile response.py
2017-07-10 20:40:42,411 INFO Registered response name with signature {'action': 'response', 'target': {'type': 'openc2:Data'}}
System check identified no issues (0 silenced).
July 10, 2017 - 20:40:42
Django version 1.10.2, using settings 'main.settings'
Starting development server at http://0.0.0.0:9000/
Quit the server with CONTROL-C.
```

> Now check that you can visit it in the browser, and login as the super-user you created.

The master's web interface is accessible on:

`http://<ip_addr>:9000/`

It's OpenC2 API is accessible on:

`http://<ip_addr>:9000/openc2/`

<div align="center">
  <a><img alt="ReactorMaster fresh dashboard" src="https://user-images.githubusercontent.com/18141485/28038959-92c7608e-65b8-11e7-9f89-b436f8d85ee0.PNG"/>
  </a>
</div>

> It is recommended you put this behind an SSL reverse proxy such as [NGINX](http://hg.nginx.org/nginx/) as commands can contain sensitive information, and connections to this box should be IP locked to known and trusted upstream orchestrators.

---

## Usage

### [ReactorMaster](https://github.com/OpenC2-org/ReactorMaster)   -   `:9000`

##### Relay Link

Follow the documentation for [ReactorRelay](https://github.com/OpenC2-org/ReactorRelay) for each relay being configured, and then return here to link them to the master and synchronise their capabilities.

With the relay(s) created, the first step is to link with the master - This can be done by clicking _*Create New Relay*_ from the main dashboard view. The URL specified should be the OpenC2 API _*(usually `/openc2/`)*_. The username and password should be the password you generated when running `createsuperuser` on the downstream relay.

<div align="center">
  <a><img alt="ReactorMaster create relay" src="https://user-images.githubusercontent.com/18141485/28038961-95e82492-65b8-11e7-930b-9d5f57c1500f.PNG"/>
  </a>

  <a><img alt="ReactorMaster relay created" height="250" width="350" src="https://user-images.githubusercontent.com/18141485/28038969-9b21b0c2-65b8-11e7-8b6e-4c25523130bb.PNG"/>
  </a>
  <a><img alt="ReactorMaster relay details" height="250" width="350" src="https://user-images.githubusercontent.com/18141485/28038980-a12ec0cc-65b8-11e7-8b89-747e958ca33d.PNG"/>
  </a>
</div>

##### Sync Capabilities

Once your relay is configured, click _*Sync Capabilities*_, this will request a list of all configured capabilities from all downstream relays. This then provides the list of actions that can be taken from the central orchestrator. If the error _*Sync Failed*_ occurs, ensure that the url have specified is the fully qualified OpenC2 API url e.g. `http://10.20.30.40:8000/openc2/` - _*Note the trailing slash*_. Make sure this is accessible from the Orchestrator. 

If syncing still fails, this could be because you have entered incorrect credentials for the relay, which will require you to delete the relay in the _*Live Relay*_ section and re-create it with the correct credentials.

<div align="center">
  <a><img alt="ReactorMaster capabilities synced" src="https://user-images.githubusercontent.com/18141485/28039086-f320e8ce-65b8-11e7-8906-8ca7cb5c9582.PNG"/>
  </a>
</div>

##### Target Creation

Targets are a standardised way to express variables to pass to profiles, for example the IP of an attacker you wish to block. In Reactor we are still using [CybOX 2.1](https://cyboxproject.github.io/releases/2.1/), however the codebase is expandable to take any kind of JSON object.

<div align="center">
  <a><img alt="ReactorMaster create target" src="https://user-images.githubusercontent.com/18141485/28038971-9c9e1f12-65b8-11e7-9d8c-25e77ab946ba.PNG"/>
  </a>
</div>

##### Job Creation

This allows the user to create a job, linking a capability with a target. Once actioned - it will be picked up by the `/cron/launcher/` view within *60* seconds _*(ensure you have created the cron job for the master)*_. Responses, errors and job status can then be tracked by clicking on the job in the GUI.

<div align="center">
  <a><img alt="ReactorMaster create target" src="https://user-images.githubusercontent.com/18141485/28038975-9f4ebb04-65b8-11e7-89fe-b5caf5ac7e0c.PNG"/>
  </a>
  
  <a><img alt="ReactorMaster job pending" src="https://user-images.githubusercontent.com/18141485/28187337-4754098a-6816-11e7-80e8-3ecf202cc68b.PNG"/>
  </a>
  
  <a><img alt="ReactorMaster job statuses" src="https://user-images.githubusercontent.com/18141485/28187331-42bd1e0c-6816-11e7-8d6d-5177f84c045e.PNG"/>
  </a>
</div>

Job progress can be tracked and the status will transition from `Sent` to `Pending` to `Success`, or `Failed` if an error occurred.

---

### Creator

<div align="center">
  <p style="color:blue;font-size:28px;"><strong>Adam Bradbury</strong></p>
  </br>
</div>
<div align="center">
  <a href="https://github.com/AdamTheAnalyst"> <img alt="AdamTheAnalyst" height="50" width="50" src="https://user-images.githubusercontent.com/18141485/28211297-cac67320-6893-11e7-98ae-5c0825229fe5.png"/>
  </a>
  <a href="https://twitter.com/adamtheanalyst"> <img alt="AdamTheAnalyst" height="50" width="50" src="https://user-images.githubusercontent.com/18141485/28211298-cac99276-6893-11e7-818f-3f7873b5d09a.png"/>
  </a>
</div>

---

## Appendices

### Reactor and OpenC2 architectural overview

```
    ┌────────┐              ┌───────┐            ┌──────────┐
    | Master ├─ manages a ─→| Relay ├─ has an ──→| Actuator |
    └─┬────┬─┘              └───────┘            └────┬─────┘
      |    |                                          |
      |    └──── defines                           can use
      |             |                                 |
  specifies         ↓                                 ↓
      |          ┌─────┐                        ┌────────────┐
      |          | Job |←───────── used by  ────┤ Capability │
      |          └──┬──┘                        └────────────┘
      ↓             |
  ┌────────┐      targets
  │ Target |←───────┘
  └────────┘
```

### Reactor project deployment file overview

```shell
.
├── LICENSE
├── README.md
├── main
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── reactor_master
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── decorators.py
│   ├── fixtures
│   │   └── initial_data.json
│   ├── forms.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── profiles
│   │   ├── __init__.py
│   │   └── response.py
│   ├── response.py
│   ├── templates
│   │   └── reactor_master
│   ├── templatetags
│   │   ├── __init__.py
│   │   └── tags.py
│   ├── tests.py
│   ├── validators.py
│   └── views.py
├── requirements.txt
├── samples
│   └── response_ack.json
└── static
    └── theme
        ├── css
        ├── font-awesome
        ├── fonts
        └── js
```

<br/>

<a href="#top">↥ back to top
