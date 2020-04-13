1. Build the Docker container:
docker build -f Dockerfile.frontend -t ralf/weather-dash-frontend ..

2. Run the Docker container:
docker run -e BASEDIR=/opt/weather-data -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -v /opt/weather-data:/opt/weather-data -p 8000:8000 ralf/weather-dash-frontend

docker run -e BASEDIR=/opt/dbdir -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -v /tmp/pycharm_project_788/remote_weather_access_v2:/opt/dbdir -p 8000:8000 ralf/weather-dash-frontend

