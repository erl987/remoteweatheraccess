# Web application for providing weather data from various stations within a weather network

## Running the whole application stack

No separate container building is required. Just run `docker-compose up` from the root directory of the project.

Then the application is accessible on http://server. This configuration is only intended for development and 
documentation purposes. A production environment should run behind HTTPS.


## Running components separately

### Database

This starts a simple database, the data lifetime is identical to that of the container:

`docker run -d --network=host -e POSTGRES_PASSWORD=passwd -p 5432:5432 postgres`


### Backend

1. Build the Docker container:

    `docker build -f Dockerfile.backend -t backend .`
    
2. Run the Docker container (expecting the PostgreSQL-database running on the localhost):

    `docker run --network=host -e JWT_SECRET_KEY=SECRET-KEY -e DB_PASSWORD=passwd -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -p 8000:8000 backend`

    The backend is now accessible via http://server:8000.
    

## Frontend

1. Build the Docker container:

    `docker build -f Dockerfile.frontend -t frontend .`

2. Run the Docker container (expecting the backend running on the localhost):

    `docker run --network=host -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -p 8050:8050 frontend`

    The frontend is now accessible via http://server:8050.
