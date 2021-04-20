# oTree HR

oTree HR is a project that aims to connect oTree with online recruiting & payment platforms like
MTurk, Prolific, Venmo, PayPal, etc, to facilitate payments, communication, and management of your workers. 
Currently it is an **beta version**, and supports:

-   MTurk: publishing HITs with micro-batching, which reduces MTurk's fees.
-   Prolific: coordinating start links, completion URLs, and payments. 

The project is ready for anyone who wants to clone it and add their own functionality, such as:

MTurk:
-	sending custom bonuses and messages to workers
-	better UI for reviewing/accepting/rejecting HITs
-	creating HITs automatically on a schedule.
-	Keeping track of which workers were paid
-   Changing HIT expiration dates
-	Configuring the exact number of assignments vs participants (oTree uses 2x by default)
-	Grant qualifications according to whatever logic you specify

Other:
-   Sending payments via PayPal/Venmo/etc.
-   Reading URL query strings from incoming participants and sending them to oTree via the "participant vars" API endpoint.

**I welcome community contributions!**
Please send an email to chris@otree.org.

## Details

It uses [oTree's REST API](https://otree.readthedocs.io/en/latest/misc/rest_api.html). 

The application is basically a middleman between oTree and the cloud. When you post a study to MTurk,
the workers click a link that takes them to your oTree HR site, and then redirects them to the correct session
in oTree. It is totally separate from oTree's built-in MTurk functionality.

oTree HR supports multiple user accounts. Each user can register any number of oTree sites. 
This means that oTree HR can be provided as a hosted service
so that people don't have to set up their own server.

## How do I run it?

First, make sure you are on the latest 5.x (`pip install -U otree`).

### On Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Locally
It's a standard Django project:

```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8005
```

You can run it on any port. Just don't use 8000 because oTree uses that port by default and you need both oTree and 
oTree HR to be running at the same time (since they communicate via API calls).

To access the admin and view the database, make a superuser:

```
python manage.py createsuperuser --username a@example.com --email a@example.com
```

If deploying to Heroku via git, make sure to set the SECRET_KEY config var.

## Why a separate project and not part of oTree?

-   It's easier for people to contribute to this project without having to know all the internals of oTree
    or coordinate merges with me.
-   This project can have its own release schedule, which is likely to be different from oTree's.
-   This project can make its own architectural decisions (e.g. database/ORM/task queue/frontend)
-   This type of code does not belong in an app development framework
-   Keeps complexity out of oTree core
