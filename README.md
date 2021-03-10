# oTree HR

oTree HR is a project that aims to connect oTree with online recruiting & payment platforms like
MTurk, Prolific, Venmo, PayPal, etc, to facilitate payments, communication, and management of your workers. 
Currently it is an **early alpha preview**, and just supports publishing HITs to MTurk (with micro-batching, which reduces 
MTurk's fees). However, it can easily be extended to do things like the following:

MTurk:
-	sending custom bonuses and messages to workers
-	better UI for reviewing/accepting/rejecting HITs
-	creating HITs automatically on a schedule.
-	Keeping track of which workers were paid
-   Changing HIT expiration dates
-	Configuring the exact number of assignments vs participants (oTree uses 2x by default)
-	Grant qualifications according to whatever logic you specify

Other:
-	Integration with Prolific and other cloud services
-   Sending payments via PayPal/Venmo/etc.

**I welcome community contributions of new functionality!**
Please send an email to chris@otree.org.

## Details

It uses [oTree's REST API](https://otree.readthedocs.io/en/latest/misc/rest_api.html). 
oTree 3.4+ and 5+ are both supported.
 
The application is basically a middleman between oTree and the cloud. When you post a study to MTurk,
the workers click a link that takes them to your oTree HR site, and then redirects them to the correct session
in oTree. It is totally separate from oTree's built-in MTurk functionality.

oTree HR supports multiple user accounts. Each user can register any number of oTree sites. 
This means that oTree HR can be provided as a hosted service
so that people don't have to set up their own server.

It can also be deployed in 1 click via a Heroku Button (see below prototype).

## How do I run it?

First, make sure you are on the latest 5.x (`pip install -U otree`),
or on oTree 3.4 beta (`pip install -U "otree<5" --pre`).

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

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Why a separate project and not part of oTree?

-   It's easier for people to contribute to this project without having to know all the internals of oTree
    or coordinate merges with me.
-   This project can have its own release schedule, which is likely to be different from oTree's.
-   This project can make its own architectural decisions (e.g. database/ORM/task queue/frontend)
-   This type of code does not belong in an app development framework
-   Keeps complexity out of oTree core
