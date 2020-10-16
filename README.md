# Full-stack web application for realizing a weather network on the internet

This is providing a website for a weather network with many remote weather stations. The software is running on a
server - in the cloud or even on small devices such as as a Raspberry Pi. The clients can be any weather station that
is capable to connect to the internet via HTTP. Usually this will be an IoT-device such as as Raspberry Pi connected
to a weather station via USB.

The frontend is currently only localized to German.

![Frontend Screenshot](/images/screenshot-main-page.png)


## Technology stack

* frontend: written in Python using the framework `dash`
* backend: written in Python using the framework `flask`
* database: `PostgresSQL`


## Installation

### Server

The server application can in principle be deployed using `docker-compose`. There are configuration files for
Google App Engine available in the codebase which can be used to develop a deployment for the Google Cloud Platform. The
server is written in Python using the `flask`-framework using a `PostgreSQL`-database. It can therefore be deployed to 
a wide variety of cloud services and even a Raspberry Pi.


### Client

At the current stage no client application is part of the project. The client is communicating with the server via
HTTP using a REST-API. This makes it easy to implement a client application tailored to the actually used weather 
station.


## Running the server application

### Running the whole application stack with `docker-compose`

It is easy to run the whole server application stack with `docker-compose`. This also includes a database. **The
database will be deleted when destroying the `postgres`-container!** This configuration is only intended for development 
and documentation purposes. A production environment should run behind HTTPS and the database volume needs to be 
persistent.

1. Change to the root directory of the project:
```shell script
  cd weatherstation
```

2. Build the containers:
```shell script
  docker-compose build
```

3. Run the stack:
```shell script
  docker-compose up
```

4. The application is now accessible on http://server.
   **You need to create at least one weather station and a push user for each station in order to run the server in a 
   meaningful way.** Check the documentation below to perform the initial configuration and get started.

5. Stop the stack:
```shell script
  docker-compose down
```


### Running components separately

#### Database

This starts a simple database, the data lifetime is identical to that of the container:

```shell script
  docker run -d --network=host -e POSTGRES_PASSWORD=passwd -p 5432:5432 postgres
```


#### Backend

1. Build the Docker container:

```shell script
  docker build -f Dockerfile.backend -t backend .
```
    
2. Run the Docker container (expecting the PostgreSQL-database running on the `localhost`):

```shell script
  docker run --network=host -e JWT_SECRET_KEY=SECRET-KEY -e DB_PASSWORD=passwd -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -p 8000:8000 backend
```

  The backend is now accessible via http://server:8000.
  
  
#### Frontend

1. Build the Docker container:

```shell script
  docker build -f Dockerfile.frontend -t frontend .
```

2. Run the Docker container (expecting the backend running on the localhost):

```shell script
  docker run --network=host -e GUNICORN_WORKERS=4 -e GUNICORN_ACCESSLOG=- -p 8050:8050 frontend
```

   The frontend is now accessible via http://server:8050.


### Deployment to Google Cloud Platform

The deployment requires the following components in the GCP:

* Google App Engine (GAE)
* Cloud-SQL (Postgres)
* Google Secrets (for storing the database credentials)
* Google VPC-connector (to connect GAE backend and SQL-database)


The GAE configuration files `backend.app.yaml` and `frontend.app.yaml` are examples showing how the server can be
deployed to two separate services `backend` and `default`. It is necessary to adjust the names / IP-addresses of the
underlying infrastructure (such as address of the backend and of the SQL-database) before applying them.

```shell script
  gcloud app deploy ./frontend/frontend.app.yaml ./backend/backend.app.yaml
```


## Get started in a production environment

The server software will not prepare the database automatically in a production environment (such as Google App Engine)
in contrast to the `docker-compose` deployment. The Python-script `prepare_database.py` allows to bootstrap the 
application in a production environment.

1. It needs to be executed on a machine that can access the database. It will set up the database tables but also 
   create a first `default_admin` user. **This user should only be used to create an own admin user and should be 
   deleted afterwards!**

2. Log in as admin user via the REST-API

3. Create the weather stations using the REST-API

4. Create a user for each weather station (expecting that the stations have already been created) using the REST-API

Now it is possible to send weather data to the server. The frontend will automatically update with 5 minutes 
delay due to caching.


## Concepts

### Users

There are three access levels for the `backend` depending on the privacy and sensitivity of the data:

* anonymous user (can get weather data for example)
* push user (can send weather data from a station to the server)
* admin user (can perform all operations, including creating and deleting resources such as users and stations)


### Weather stations

Each weather station is defined by a name (such as `MUC`) and is created via the REST-API. It is linked to a push
user that can send data from this station to the server.


### Sensors

The weather sensors are currently hard-coded and represent the usually available sensors.


## REST-API

The REST-API allows to perform all required user operations following the CRUD-pattern:

* handling users (create, get, change, delete)
* handling weather data (create, get, change, delete)
* handling stations (create, get, change, delete)
* handling sensors (they are hard-coded right now, therefore only get)

There are examples for all REST-API operations in the directory `backend/tests/requests`.

Once the server is configured with users and stations, weather data can be sent to the server from the client by a
`PUT` HTTP-request. Before that, the weather station user has to login in to obtain a JWT access-token. Multiple
time points can be sent at once by using an array instead.

```http request
POST https://{{url}}/api/v1/login
Content-Type: application/json

{
  "name": "user1",
  "password": "passwd"
}
```

```http request
PUT https://{{url}}/api/v1/data
Content-Type: application/json
Authorization: Bearer jwt-access-token

{
  "timepoint": "2019-07-06T12:34:20+02:00",
  "station_id": "TES",
  "pressure": 1015.5,
  "uv": 9.3,
  "rain_counter": 1230.5,
  "temperature_humidity": [
    {
      "sensor_id": "OUT1",
      "temperature": 18.3,
      "humidity": 90.5
    },
    {
      "sensor_id": "IN",
      "temperature": 23.5,
      "humidity": 63.5
    }
  ],
  "speed": 89.5,
  "gusts": 103.5,
  "direction": 190.5,
  "wind_temperature": 16.5
}
```


## Tests

The codebase has a high coverage of unit tests. The tests for the backend are expecting a running `postgres` database
on the `localhost`. The most easy way to provide an empty database is to start a `postgres` container:

```shell script
  docker run -d --network=host -e POSTGRES_PASSWORD=passwd -p 5432:5432 postgres
```


# License 
   
Remote Weather Access - Client/server solution for distributed weather networks
 Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
