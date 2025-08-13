# SRL Platform

Minimal Django platform to support self-regulated learning with optional AI assistance.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # adjust values
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo  # optional demo data
python manage.py runserver
```

Access the site at `http://localhost:8000/`.

### Environment

The `.env` file configures runtime settings:

- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `OPENAI_API_KEY`

## Frontend flows

- `/goal/kg/` – goal setting without AI (Kontrollgruppe, *KG*)
- `/goal/vg/` – AI-assisted goal coaching (Versuchsgruppe, *VG*)

## API quickstart

### Goal endpoints

- `POST /api/goals/` – create goal for *KG*; returns final goal with SMART score
- `POST /api/vg/goals/` – create goal for *VG* and start coaching dialogue
- `POST /api/vg/coach/next/` – continue dialogue (`goal_id`, optional `user_reply`)
- `POST /api/vg/goals/finalize/` – finalize goal after coaching
- `POST /api/vg/next-step/suggest/` – get or store reflection next steps for *VG*

### Export endpoints

- `GET /api/export/csv/`
- `GET /api/export/xlsx/`

Both endpoints require a staff user and support filters via query params:
`from`, `to` (YYYY-MM-DD), `class` (e.g. `10A`), `group` (`VG` or `KG`).

## Tests

```bash
python manage.py test
```

The tests cover API flows and verify the export filters.
