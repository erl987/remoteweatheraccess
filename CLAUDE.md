# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Remote Weather Access is a full-stack weather network: remote weather stations push data over HTTP to a
server application, which serves a public German-language web frontend. It consists of **four independently
deployable Python components**, each with its own `requirements.in` / `requirements.txt` and its own test suite:

| Directory   | Component | Framework | Deployed as |
|-------------|-----------|-----------|-------------|
| `backend/`  | REST API (`/api/v1`) | Flask + SQLAlchemy + JWT | Cloud Run (gunicorn/gevent) |
| `frontend/` | Public website | Django + `django_plotly_dash` (Dash/Plotly) | Cloud Run (gunicorn) |
| `export/`   | Monthly CSV exporter | FastAPI | Cloud Run, triggered by Cloud Scheduler |
| `client/`   | Weather-station agent | plain Python + FastAPI health endpoint | Docker on a Raspberry Pi |

## Commands

All test commands are run **from the repository root**; each component needs its own directory on
`PYTHONPATH` (the test modules import `backend_src.*`, `client_src.*`, `export_src.*` etc. as top-level packages).

```shell
# backend - REQUIRES a running Postgres on localhost:5432 (user postgres / password passwd)
docker run -d -e POSTGRES_PASSWORD=passwd -p 5432:5432 postgres
PYTHONPATH=$PWD/backend pytest backend/tests/unit_tests

# frontend (no database needed, uses SQLite + frontend/environments/.frontend.testing.env via pytest.ini)
PYTHONPATH=$PWD/frontend pytest frontend/tests

# exporter (note the doubled `tests/tests` path)
PYTHONPATH=$PWD/export pytest export/tests/tests

# client
PYTHONPATH=$PWD/client pytest client/tests

# a single test / single file
PYTHONPATH=$PWD/backend pytest backend/tests/unit_tests/test_user.py::test_create_user
```

Overriding the Postgres host/password for the backend tests: `POSTGRES_TEST_URL`, `DB_PASSWORD`
(see `TestConfig` in `backend/backend_config/settings.py`).

Running the stack locally:

```shell
docker-compose up          # whole stack incl. Postgres, MinIO and an nginx reverse proxy on http://localhost
python3 backend/backend_app.py   # backend only, on :8000, uses DevConfig against localhost Postgres
```

Frontend standalone (needs the env vars, see README.md for the full list):

```shell
cd frontend/django_frontend
export DJANGO_SETTINGS_MODULE=django_frontend.settings ENV_PATH=../environments/.frontend.ide.env \
       TEST_MODE=true BRAND_NAME="Das Wetternetzwerk" PYTHONPATH=$PYTHONPATH:/path/to/repo/root
python3 manage.py runserver
```

Dependencies are managed with **pip-tools**: edit `<component>/requirements.in` or `dev-requirements.in`, then
`pip-compile requirements.in` inside that component's directory. Never hand-edit the `.txt` files; Renovate keeps
them updated automatically (minor/patch auto-merge).

There is no linter configured in CI — the pipeline only runs the four pytest jobs, then builds and deploys.

## Architecture

### Data flow

`client` reads the station via the `te923con` binary → POSTs gzipped JSON arrays to `backend` `/api/v1/data`
→ `frontend` never touches the weather database, it pulls everything through the REST API via
`CachedBackendProxy` → in parallel, `export` pulls the same API monthly and writes PC-Wetterstation-compatible
CSV files into a GCS bucket, which the frontend's download page reads directly from that bucket.

The frontend caching (5 minutes, in `dash_weatherpage/backend_proxy.py`) is why new data only shows up on the
website with a delay.

### Backend

- Blueprints per resource under `backend_src/{user,station,sensor,temp_humidity_sensor,weatherdata}/`, each with
  `routes.py` and marshmallow `schemas.py`. All blueprints are registered in `backend_app.create_app()`.
- **Two databases via SQLAlchemy binds**: the default bind holds `FullUser`, everything with
  `__bind_key__ = 'weather-data'` (stations, sensors, datasets) lives in a second database with its own
  credentials. Both are configured in `backend_config/settings.py` (`ProdConfig` / `DevConfig` / `TestConfig`).
- Every route is wrapped in two decorators from `backend_src/utils.py`:
  `@access_level_required(Role.X)` (JWT role check; `ADMIN` implicitly satisfies every level, `PUSH_USER`
  additionally may only write data for its own `station_id`) and
  `@json_with_rollback_and_raise_exception` / `@with_rollback_and_raise_exception`, which translate exceptions
  into `APIError`s with proper HTTP status codes and always roll back and close the session. Follow this pattern
  for new routes rather than handling errors inline.
- Roles are `GUEST`, `PULL_USER` (unused), `PUSH_USER`, `ADMIN` (`Role` enum in `backend_src/utils.py`).
- **Sensors are hard-coded**, not user-manageable: `generate_sensors()` in `backend_src/sensor/models.py` and
  `generate_temp_humidity_sensors()` in `backend_src/models.py`; descriptions there are German and surface
  directly in the UI. `dewpoint` and `rain`/`rain_rate` are computed, not stored.
- `prepare_database()` (called on startup and by `backend/prepare_database.py`) creates the tables and, when the
  user table is empty, a `default_admin` with a random password logged as a warning.

### Frontend

- Django serves thin template views (`weatherpage/views.py`) that embed two `DjangoDash` apps registered by
  importing `dash_weatherpage_app.py` and `dash_download_page_app.py` — the import in `views.py` has the side
  effect of registering the apps, so it must not be removed.
- `dash_weatherpage/` is the main plotting page (station/sensor/time-period selection, responsive via
  `dash-breakpoints`); `dash_download_page/` is the CSV download page backed by the exporter's GCS bucket.
- Configuration comes from an **env file selected by the `ENV_PATH` variable** (`frontend/environments/.frontend.*.env`)
  read by `django-environ`, plus Google Secret Manager when running on GCP. `django_frontend/google_cloud_utils.py`
  decides which path applies; `TEST_MODE=True` forces the non-GCP path.
- Sensor ids in the frontend are composites of a temp/humidity sensor id and a marker suffix
  (`OUT1_temp`, `OUT1_humid`, `OUT1_dewpoint`) and get split back into API parameters in `backend_proxy.py`.

### Deployment

GitLab CI (`.gitlab-ci.yml`) runs tests → builds the three server images → deploys to GCP Cloud Run. `master`
deploys to the production project, every other branch/MR to the testing project (review environments, torn down
via the manual `stop review` job). Cloud Run service definitions are the `envsubst`-templated YAMLs in
`deployment/google_cloud_run/`; Django migrations and `collectstatic` run through Cloud Build
(`deployment/google_cloud_build/cloudmigrate.yaml`). Environment-specific values come from
`deployment/environments/.{production,testing}.env` plus GitLab CI variables (documented in README.md).

## Conventions

- Every source file starts with the AGPL-3.0 copyright header (see any existing `.py`, `.yaml` or `Dockerfile`);
  add it to new files.
- User-facing strings and sensor descriptions are German; code, comments and log messages are English.
- Timepoints are timezone-aware ISO 8601. The backend serialises `datetime` via a custom Flask JSON provider
  (`IsoDateTimeJSONProvider`) and localises naive timepoints to the `TIMEZONE` setting (default `Europe/Berlin`).
- `backend/tests/requests/**.http` and `export/tests/requests/*.http` are runnable JetBrains HTTP-client examples
  covering every REST endpoint — the fastest way to see the exact request/response shape of an endpoint.
  They read credentials from the (untracked-in-spirit) `http-client.env.json` files next to them.
- Backend test fixtures (authenticated clients, sample datasets) all live in `backend/tests/utils.py` and are
  imported explicitly into each test module; there are no `conftest.py` files anywhere in this repository.
