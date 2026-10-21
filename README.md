# Wazimba Rugby 7s

A full-stack starter for the Wazimba Rugby 7s management, performance, learning and archive system.

## Stack

- Frontend: React, JavaScript and Vite
- API: Python, Django REST Framework
- Database: PostgreSQL
- Authentication: Django REST Framework token authentication

## Implemented modules

- Role-aware sign-in; authenticated reads and staff-only record changes
- Dashboard, player profiles, season registration, tournaments, fixtures/results and team events with attendance
- Training sessions and attendance; match participation and player statistics
- Team analytics, player performance, season summaries, post-match reviews and CSV reports
- Announcements and source links; laws, tactics and video resource links
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

The API runs at `http://127.0.0.1:8000/api/`; API documentation is at `http://127.0.0.1:8000/api/docs/`. The frontend uses the API as its default base. Sign in with the Django account you create. Staff users can manage records; regular authenticated users can view them.

## API routes

- `POST /api/auth/token/` — obtain an authentication token
- `GET /api/dashboard/` — dashboard totals and upcoming activity
- `/api/players/`, `/api/seasons/`, `/api/season-registrations/`, `/api/tournaments/`, `/api/matches/`, `/api/match-participations/`, `/api/training-sessions/`, `/api/training-attendance/`, `/api/team-events/`, `/api/team-event-attendance/`, `/api/announcements/`
- `/api/performance/team/`, `/api/performance/players/`, `/api/reports/`, `/api/reports/csv/`
- `/api/learning-resources/`, `/api/media/`, `/api/injury-records/`, `/api/alumni/`, `/api/match-reviews/`
- Record writes require a staff account; injury and welfare records are staff-only. Media without recorded consent and alumni contact email without consent are hidden from regular members.
- `/api/schema/` — OpenAPI schema
- `/admin/` — Django administration

## Checks

From `frontend/`, run `npm test` and `npm run build`. From `backend/`, activate your virtual environment and run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test team.tests`.

## Notes

Set `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `DATABASE_URL` in the deployment environment. The media gallery currently stores authorized media links rather than uploading files. Medical and welfare records need deployment storage, consent, and access policies before production use.
