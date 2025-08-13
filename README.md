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
python manage.py runserver
```

Access the site at `http://localhost:8000/`.
