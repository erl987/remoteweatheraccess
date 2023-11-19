# Full-stack web application for realizing a weather network on the internet

This is providing a website for a weather network with many remote weather stations. The software is running on a
server - in the cloud or even on small devices such as a Raspberry Pi. The clients can be any weather station that is
capable to connect to the internet via HTTP. Usually this will be an IoT-device such as a Raspberry Pi connected to a
weather station via USB.

The frontend is currently only localized to German.

![Frontend Screenshot](/images/screenshot-main-page.png)

## Technology stack

* frontend: written in Python using the frameworks `django` and `dash`
* backend: written in Python using the framework `flask`
* database: `PostgresSQL`
* client: written in Python

## Installation

### Server

The server application is deployed with Google Cloud Run. It can in principle also be deployed using `docker-compose`.
The server is written in Python using the `flask`-framework using a `PostgreSQL`-database. It can therefore be deployed
to a wide variety of cloud services and even a Raspberry Pi.

### Client

There is a client available for weather stations of type TE923. It is designed to run on minicomputers with
ARM-processors such as a Raspberry Pi 2+. It can also run on other types of computers with small adaptions. This fully
configurable client is reading the latest data from the weather station and is sending it to the server via the
REST-API. It is deployed using Docker.

## Running the server application

### Running the whole application stack with `docker-compose`

It is easy to run the whole server application stack with `docker-compose`. This also includes a database. **The
database will be deleted when destroying the `postgres`-container!** This configuration is only intended for development
and documentation purposes. A production environment should run behind HTTPS, and the database volume needs to be
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
   **You need to create at least one weather station, and a push user for each station in order to run the server
   meaningfully.** Check the documentation below to perform the initial configuration and get started.

5. Stop the stack:
    
    ```shell script
      docker-compose down
    ```

### Running components separately

#### Database

This starts a simple database, the data lifetime is identical to that of the container:

```shell script
  docker run -d -e POSTGRES_PASSWORD=passwd -p 127.0.0.1:5432:5432 postgres
```

#### Backend

```shell script
  python3 backend/backend_app.py
```

The backend is now accessible via http://server:8000.

#### Frontend

```shell script
  cd frontend/django_frontend
  export BRAND_NAME=Das Wetternetzwerk
  export DJANGO_SETTINGS_MODULE=django_frontend.settings
  export ENV_PATH=../environments/.frontend.ide.env
  export TEST_MODE=true
  export PYTHONPATH=$PYTHONPATH:/path/to/root/of/the/repository
  python3 manage.py runserver
```

The frontend is now accessible via http://server:8050.

### Deployment to Google Cloud Platform

This project supports continuous delivery of the server components to Google Cloud Platform (GCP) through GitLab CI/CD.
It is expecting that the infrastructure is up and running, the most important expected components are:

* Google Cloud Run API activated
* Cloud-SQL (Postgres)
* Google Secrets (for storing the database credentials)
* Google Cloud Storage (for storing the static files of `django`)

The required infrastructure can be deployed through the separate subproject `infrastructure` using Terraform. In that
subproject it is exactly documented which infrastructure is required.

#### Seed project

The server components will be deployed into a separate GCP-project, they need however a service account that has all
required permissions. It should be provided in a separate *seed project* in GCP.

Create a service account such as `terraform@seed-project-123356.iam.gserviceaccount.com` in this project and assign it
the following roles:

* `Cloud SQL Admin`
* `Editor`
* `Cloud Run Admin`
* `Storage Admin`
* `Viewer`

The *seed project* requires the same APIs being activated as the project running the server components. These are:

* `secretmanager.googleapis.com`
* `containerregistry.googleapis.com`
* `run.googleapis.com`
* `sqladmin.googleapis.com`

#### GitLab variables

The following variables need to be defined in the GitLab project:

* `GCP_CONTAINER_REGISTRY` (for example `eu.gcr.io`)
* `GCP_PROJECT_ID_PRODUCTION` (for example `weather-production-123456`)
* `GCP_PROJECT_ID_TESTING` (for example `weather-testing-123456`)
* `GCP_REGION_ID` (for example `europe-west3`)
* `GOOGLE_APPLICATION_CREDENTIALS` (a *file variable*, the key for the service project used by the CI/CD pipeline to
                                    deploy to GCP)
* `BRAND_NAME` (the name of the website shown in the main header of the site, for example `Das Wetternetzwerk`)
* `DATA_PROTECTION_POLICY_HTML_FILE` (a *file variable*, the content of the data protection policy)
* `IMPRESS_HTML_FILE` (a *file variable*, the content of the impress)
* `FRONTEND_ADDRESS`(the permanent public URL of the frontend, format https://server.net)

The *production* and *testing* projects are used by the **main** branch, and the **merge request** branches
respectively.

#### Use the CI/CD pipeline

Every commit to the code base trigger the unit tests and deploys the server components to either the *production*, or
the *testing* project. The only requirement is to set up the GitLab variables as described above.

## Get started in a production environment

The server software will prepare the database automatically in a production environment (if this is setting the
environment variable `RUNNING_ON_SERVER`, which is the default) or in case of a `docker-compose` deployment.

The Python-script `prepare_database.py` allows however also to bootstrap the application in a production environment
manually if required. It needs to be executed on a machine that can access the database.

The bootstrapping - automatic or manual - will set up the database tables but also create a first `default_admin`
user. **This user should only be used to create an own admin user and should be deleted afterward!**

The further steps are in any case:

1. Log in as admin user via the REST-API

2. Create the weather stations using the REST-API

3. Create a user for each weather station (expecting that the stations have already been created) using the REST-API

Now it is possible to send weather data to the server. The frontend will automatically update with 5 minutes delay due
to caching.

## Running the client application

The client software gets deployed using Docker. Docker needs to be installed on the machine, one way is to use the
available convenience script: https://docs.docker.com/engine/install/debian/#install-using-the-convenience-script

### Configure the USB-device

In order to make the USB connection from the container to the weather
station working without root permissions, the weather station USB device needs some configuration. Execute the following
commands on the **host** machine that will run the Docker container later:

```shell
  sudo sh -c 'echo SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"1130\", ATTRS{idProduct}==\"6801\", GROUP=\"plugdev\", MODE=\"0660\" > /etc/udev/rules.d/51-usb-te923-weatherstation.rules'
  sudo udevadm control --reload-rules && sudo udevadm trigger
```

This configuration is targeting weather stations of type TE923. Other ways to achieve that are also possible if desired.

### Create the internal configuration directory

Now create a directory where the container can permanently store its internal configuration:

```shell
  sudo mkdir -p /opt/weatherstation-client/data/
  sudo chown -R <username>:<groupname> /opt/weatherstation-client/data/
```

Replace `<username>` and `<groupname>` by your actual user and group name.

### Configure the client

Clone the Git repository if not yet done and create and change the configuration file as required:

```shell
  cd weatherstation
  sudo mkdir /opt/weatherstation-client/config/
  sudo cp client/default_client_config.yaml /opt/weatherstation-client/config/client_config.yaml
  sudo nano /opt/weatherstation-client/config/client_config.yaml
```

You could use any other editor to edit the configuration file.

### Create and run the Docker container

The client software gets finally installed as described here. **Note that the `Dockerfile` is using a base image
suitable for Raspberry Pi 2+ computers**, this base image needs to be replaced by a regular Python image (such as
`FROM python:3.11.6-slim-bookworm`) for other computer architectures.

> **_NOTE:_**  **Docker Compose** must be available on the machine.

1. Change to the root directory of the project:
    
    ```shell script
      cd weatherstation/client
    ```

2. Prepare the file containing the backend API password (corresponding to the user defined in the config `yaml`-file):

    ```shell
      echo BACKEND_PASSWORD=<password> > te923-client-env.list
    ```

    Replace `<password>` by the actual password. This file should not be readable to other users. **It should be 
    deleted after starting the container as it contains sensitive data**.

3. Start the container, it will be built automatically:

   ```shell
      export GIT_COMMIT=$(git rev-parse --short HEAD)
      docker-compose up -d
   ```
   
   You can check the logs of the client Docker container like this:

    ```shell
      docker logs client-te923-weather-client-1 -t -f
    ```

4. Add a cron job to automatically restart the container if the client is not working properly:

   ```shell
      sudo cp client/deployment/weather-client-healthcheck-cron /etc/cron.d
   ```
   
   You can check the syslog to verify that the cron job runs every minute:

   ```shell
      tail -f /var/log/syslog
   ```


## Concepts

### Users

There are three access levels for the `backend` depending on the privacy and sensitivity of the data:

* anonymous user (can get weather data for example)
* push user (can send weather data from a station to the server)
* admin user (can perform all operations, including creating and deleting resources such as users and stations)

### Weather stations

Each weather station is defined by a name (such as `MUC`) and is created via the REST-API. It is linked to a push user
that can send data from this station to the server.

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
`PUT` HTTP-request. Before that, the weather station user has to login in to obtain a JWT access-token. Multiple time
points can be sent at once by using an array instead.

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

The codebase has a high coverage of unit tests. All unit tests run automatically on commits by the CI/CD-pipeline.

If running the tests manually, they are expecting a running `postgres` database on the `localhost`. The most easy way to
provide an empty database is to start a `postgres` container:

```shell script
  docker run -d -e POSTGRES_PASSWORD=passwd -p 5432:5432 postgres
```

# License

Remote Weather Access - Client/server solution for distributed weather networks Copyright (C) 2013-2023 Ralf Rettig (
info@personalfme.de)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
details.

You should have received a copy of the GNU Affero General Public License along with this program. If not,
see <https://www.gnu.org/licenses/>.
