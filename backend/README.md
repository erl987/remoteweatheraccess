# Backend Rest-API

## PostgreSQL-database

```
docker run -d -e POSTGRES_PASSWORD=passwd -p 5432:5432 postgres
```

## Proxy-server

````
docker run -d --rm -p 80:80 --network host -v /home/rarettig/weatherstation/config/nginx:/etc/nginx/conf.d nginx
````

## Running the backend
 
## With Gunicorn

```
export JWT_SECRET_KEY=SECRET-KEY
export DB_PASSWORD=passwd
gunicorn -b 0.0.0.0:8050 --config config/gunicorn.conf --log-config config/logging.conf wsgi:app
```

### As docker container

1. Build the Docker container:
```
docker build -f Dockerfile.backend -t ralf/weather-backend .
```

2. Run the Docker container:
```
docker run -e BASEDIR=/opt/weather-data -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -e JWT_SECRET_KEY=SECRET-KEY -v /opt/weather-data:/opt/weather-data -p 8000:8000 ralf/weather-backend
```
