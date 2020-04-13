1. Build the Docker container:

`docker build -f Dockerfile.frontend -t ralf/weather-dash-frontend .`


2. Run the Docker container:

`docker run -e DBBASEDIR=/opt/dbdir -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -v /var/lib/remote-weather-access:/opt/dbdir -p 8000:8000 ralf/weather-dash-frontend`

