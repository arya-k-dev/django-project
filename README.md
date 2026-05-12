# SkillExchange 1.0

SkillExchange is a Django web application for peer-to-peer skill exchange. Users can register, build a profile, list skills they can teach, list skills they want to learn, find reciprocal matches, send exchange requests, chat after a request is accepted, and rate completed exchanges.

## Current Status

The project is a local Django 4.2 application backed by SQLite. The main app modules are implemented and wired into routes:

- Accounts: signup, login, logout, profile setup/edit/view, onboarding, login history.
- Skills: categories, skills, teach/learn user skills, add/edit/delete/manage views, search and create APIs.
- Matching: reciprocal match scoring, filters, exchange requests, accept/decline/cancel/complete flows.
- Messaging: conversations created from accepted requests, inbox, chat view, message send and polling APIs.
- Ratings: completed-exchange partner ratings with overall score, teaching quality, communication, and punctuality.
- UI: Django templates plus local CSS and JavaScript under `static/`.
- Tests: smoke/API/onboarding tests are present in `skills/tests.py`; standalone signup debug scripts also exist.

Note: the checked-in virtual environments currently point to local Python paths that may not exist on another machine. Recreate the virtual environment locally before running the app or tests.

## Tech Stack

- Python 3.12 recommended
- Django `>=4.2,<5.0`
- Pillow `>=10.0`
- SQLite for local development
- Django templates, static CSS, and vanilla JavaScript

## Project Layout

```text
skillexchange 1.0/
|-- manage.py
|-- requirements.txt
|-- db.sqlite3
|-- run_project.bat
|-- debug_signup.py
|-- test_signup.py
|-- skillexchange/
|   |-- settings.py
|   |-- urls.py
|   |-- wsgi.py
|-- accounts/
|   |-- models.py        # UserProfile, LoginHistory
|   |-- views.py         # auth, profiles, onboarding
|   |-- forms.py
|   |-- signals.py       # profile creation and login history
|   |-- urls.py
|-- skills/
|   |-- models.py        # SkillCategory, Skill, UserSkill
|   |-- views.py         # skill CRUD, dashboard, APIs
|   |-- forms.py
|   |-- tests.py
|   |-- management/commands/seed_skills.py
|-- matching/
|   |-- models.py        # ExchangeRequest
|   |-- views.py         # match scoring and request workflow
|   |-- urls.py
|-- messaging/
|   |-- models.py        # Conversation, Message
|   |-- views.py         # inbox, conversation, send/poll APIs
|   |-- urls.py
|-- ratings/
|   |-- models.py        # Rating
|   |-- views.py
|   |-- forms.py
|   |-- urls.py
|-- templates/
|   |-- base.html
|   |-- sidebar_base.html
|   |-- home.html
|   |-- dashboard.html
|   |-- accounts/
|   |-- skills/
|   |-- matching/
|   |-- messaging/
|   |-- ratings/
|-- static/
|   |-- css/
|   |-- js/
|-- media/
```

## Setup

From the nested project folder that contains `manage.py`:

```powershell
cd "C:\Users\hp\OneDrive\New folder\OneDrive\Documents\skillexchange 1.0\skillexchange 1.0"
```

Create and activate a fresh virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Apply migrations and seed starter skills:

```powershell
python manage.py migrate
python manage.py seed_skills
```

Create an admin account if needed:

```powershell
python manage.py createsuperuser
```

For custom admin dashboard access, mark the user's profile as an admin:

```powershell
python manage.py shell
```

```python
from django.contrib.auth.models import User

user = User.objects.get(username="your_admin_username")
user.profile.is_admin = True
user.profile.save()
```

Run the development server:

```powershell
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`.

## Windows Helper Script

`run_project.bat` is intended to install dependencies, run migrations, seed skills, and start the server. At the moment it expects a local Python executable under `.python\Python312\python.exe`. If that folder is not present, use the manual setup steps above or update the script to point at your local Python installation.

## Main Routes

| URL | Purpose |
| --- | --- |
| `/` | Home page |
| `/dashboard/` | Logged-in user dashboard |
| `/accounts/signup/` | User registration |
| `/accounts/login/` | Login |
| `/accounts/logout/` | Logout |
| `/accounts/profile/setup/` | Initial profile setup |
| `/accounts/profile/edit/` | Edit profile |
| `/accounts/profile/<username>/` | Public profile |
| `/accounts/onboarding/step1/` | Onboarding profile step |
| `/accounts/onboarding/step2/` | Onboarding teach-skill step |
| `/accounts/onboarding/step3/` | Onboarding learn-skill step |
| `/skills/add/` | Add a teach/learn skill |
| `/skills/edit/<pk>/` | Edit a user skill |
| `/skills/manage/` | Manage user skills |
| `/skills/delete/<pk>/` | Delete a user skill |
| `/skills/api/search/` | Skill autocomplete API |
| `/skills/api/create/` | Create skill API |
| `/skills/skills/` | Skill list view |
| `/matching/` | Recommended matches |
| `/matching/send/<user_id>/` | Send exchange request |
| `/matching/requests/` | Sent and received requests |
| `/matching/respond/<pk>/` | Accept or decline request |
| `/matching/accept/<request_id>/` | Accept helper route |
| `/matching/decline/<request_id>/` | Decline helper route |
| `/matching/cancel/<request_id>/` | Cancel pending sent request |
| `/matching/complete/<pk>/` | Mark accepted exchange complete |
| `/messages/` | Inbox |
| `/messages/<conv_id>/` | Conversation view |
| `/messages/<conv_id>/poll/` | Message polling API |
| `/messages/<conv_id>/send/` | Send message API |
| `/ratings/rate/<user_id>/` | Rate exchange partner |
| `/ratings/my-ratings/` | View ratings received |
| `/admin/` | Django admin |

## Matching Logic

The reciprocal matching algorithm lives in `matching/views.py`.

```text
score = 0
score += 2 * number of skills I can teach that the other user wants to learn
score += 2 * number of skills the other user can teach that I want to learn
score += 3 if both directions have at least one match
```

Only users with a score greater than zero are returned. Users who already have an exchange request with the current user are excluded. The matches page also supports category, availability, and score sorting filters.

## Data Model Summary

- `UserProfile`: bio, avatar, location, availability, social links, verification flags, response rate, available slots, timeline milestones.
- `LoginHistory`: login timestamp, IP address, and device text.
- `SkillCategory`: category name, icon, description.
- `Skill`: skill name, category, description, approval flag.
- `UserSkill`: user-owned teach/learn skill with level, description, and years of experience.
- `ExchangeRequest`: sender, receiver, status, message, matched skill names, match score.
- `Conversation`: one-to-one with an accepted exchange request and linked participants.
- `Message`: sender, receiver, content, read state, timestamp.
- `Rating`: exchange request, rater, rated user, score, feedback, and detailed dimensions.

## Tests

Run the Django test suite after setting up a working Python environment:

```powershell
python manage.py test
```

Additional standalone scripts are available for signup troubleshooting:

```powershell
python test_signup.py
python debug_signup.py
```

Current verification note: in this workspace, test execution was blocked because the existing virtualenv launchers point to unavailable local Python executables and the system `python.exe` alias is not runnable from the shell session. Recreate the virtual environment, then run the commands above.

## Development Notes

- `DEBUG = True` and `ALLOWED_HOSTS = ['*']` are development settings.
- Static files are stored in `static/`; collected static output is in `staticfiles/`.
- Uploaded media is stored in `media/`.
- `db.sqlite3`, `media/`, virtual environments, `__pycache__/`, and `staticfiles/` are local/generated artifacts and are usually not committed in a production-ready repository.

## Production Checklist

Before deploying:

1. Move `SECRET_KEY` and other secrets to environment variables.
2. Set `DEBUG = False`.
3. Restrict `ALLOWED_HOSTS`.
4. Use a production database such as PostgreSQL.
5. Configure static and media file hosting.
6. Add HTTPS.
7. Review authentication, CSRF, email, logging, and backup settings.
