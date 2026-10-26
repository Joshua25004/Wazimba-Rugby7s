# Wazimba Rugby 7s

A full-stack starter for the Wazimba Rugby 7s management, performance, learning and archive system.

## Stack

- Frontend: React, JavaScript and Vite
- API: Python, Django REST Framework
- Database: PostgreSQL
- Authentication: Django REST Framework token authentication

## Implemented modules

- Member, staff and administrator roles; public member-only registration, server-verified sign-in, logout, and expiring password-reset links
- Dashboard, player profiles, season registration, tournaments, fixtures/results and team events with attendance
- Training sessions and attendance; match participation and player statistics
- Team analytics, player performance, season summaries, post-match reviews and CSV reports
- Staff-managed original and curated Kenyan/international rugby articles with a featured carousel, laws and tactics resources, and uploaded or embedded learning videos
- Media-link gallery with consent visibility, staff-only welfare records, alumni and archive views

Analytics are computed from saved database records. Empty data produces explicit empty states; the frontend does not substitute demonstration players or scores.

## Run locally

1. Start PostgreSQL with `docker compose up -d db`, or create a database manually. In the backend terminal set `$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/wazimba_rugby"` (PowerShell) to use PostgreSQL. If `DATABASE_URL` is unset, the backend uses SQLite for a quick development run.
2. Start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

3. Start the frontend in another terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

The API runs at `http://127.0.0.1:8000/api/`; API documentation is at `http://127.0.0.1:8000/api/docs/`. The frontend uses the API as its default base. Create the first administrator with `createsuperuser`; existing superusers map to administrators and pre-existing `is_staff` accounts map to staff when migrations run. Public registrations are always members. Staff manage team records; administrators manage accounts and roles. Injury records require explicitly assigned welfare access.

## API routes

- `POST /api/auth/token/` — obtain an authentication token
- `GET /api/auth/me/` and `POST /api/auth/logout/` — verify and revoke a token session
- `POST /api/auth/register/` — create a member account only
- `POST /api/auth/password-reset/` and `/api/auth/password-reset/confirm/` — request and apply expiring password reset tokens
- `/api/admin/accounts/` — administrator-only account search and role/status management
- `GET /api/dashboard/` — dashboard totals and upcoming activity
- `/api/players/`, `/api/seasons/`, `/api/season-registrations/`, `/api/tournaments/`, `/api/matches/`, `/api/match-participations/`, `/api/training-sessions/`, `/api/training-attendance/`, `/api/team-events/`, `/api/team-event-attendance/`, `/api/announcements/`
- `/api/performance/team/`, `/api/performance/players/`, `/api/reports/`, `/api/reports/csv/`
- `/api/news/` — published articles, curated source links, image uploads, featured status, and article details
- `/api/learning-resources/`, `/api/media/`, `/api/injury-records/`, `/api/alumni/`, `/api/match-reviews/`
- Record writes require staff or administrator roles; injury and welfare records require assigned welfare access. Media without recorded consent and alumni contact email without consent are hidden from regular members.
- `/api/schema/` — OpenAPI schema
- `/admin/` — Django administration

## Checks

From `frontend/`, run `npm test` and `npm run build`. From `backend/`, activate your virtual environment and run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test team.tests`.

## Notes

Set `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `DATABASE_URL` in the deployment environment. PostgreSQL is supported through `DATABASE_URL`; the active local database is SQLite, so PostgreSQL connectivity has not been verified here.

Password reset uses Django's expiring token generator. Local development defaults to Django's console email backend, which prints reset links in the backend terminal. Production must configure SMTP through `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, and `PUBLIC_FRONTEND_URL`.

Learning-resource video files (MP4/WebM/Ogg, up to 500 MB) are stored under `MEDIA_ROOT`; external embeds are limited to YouTube/Vimeo. Local development serves media only with `DEBUG=True`. Production must mount durable media storage or configure object storage and its URL before uploads are production-ready. News records support original Wazimba articles and staff-curated third-party links; no licensed live news provider or API key is configured. Administrator account changes are recorded in the application activity log.
