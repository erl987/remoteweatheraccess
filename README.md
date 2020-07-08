# Web application for providing weather data from various stations within a weather network

## Backend database

As a backend database SQLITE is used, the database file needs to be present on the localhost.


## Running the whole application stack

No separate container building is required. Just run `docker-compose up` from the root directory of the project.

Then the application is accessible on http://server. This configuration is only intended for development and 
documentation purposes. A production environment should run behind HTTPS.


## Running the frontend container separately

1. Build the Docker container:

    `docker build -f Dockerfile.frontend -t weather-dash-frontend .`


2. Run the Docker container:

    `docker run -e DBBASEDIR=/opt/dbdir -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -v /home/rarettig/weatherstation/frontend/test_data:/opt/dbdir -p 8050:8050 weather-dash-frontend`

    You need to adapt the directory containing the database. The frontend is accessible via http://server:8050.
