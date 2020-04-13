1. Build the Docker container:
docker build -f Dockerfile.backend -t ralf/weather-backend .

2. Run the Docker container:
docker run -e BASEDIR=/opt/weather-data -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -e JWT_SECRET_KEY=SECRET-KEY -v /opt/weather-data:/opt/weather-data -p 8000:8000 ralf/weather-backend

