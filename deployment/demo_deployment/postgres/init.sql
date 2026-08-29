/*
 * Remote Weather Access - Client/server solution for distributed weather networks
 *  Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as
 *  published by the Free Software Foundation, either version 3 of the
 *  License, or (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
-- DO NOT DEFINE THE PASSWORDS LIKE THIS IN PRODUCTION
-- each database is owned by its application user: since Postgres 15 a user that only holds
-- database-level privileges cannot create objects in the `public` schema of that database
CREATE USER userdb;
ALTER USER userdb WITH PASSWORD 'passwd1';
CREATE DATABASE users OWNER userdb;
GRANT ALL PRIVILEGES ON DATABASE users TO userdb;

CREATE USER weatherdatadb;
ALTER USER weatherdatadb WITH PASSWORD 'passwd2';
CREATE DATABASE weatherdata OWNER weatherdatadb;
GRANT ALL PRIVILEGES ON DATABASE weatherdata TO weatherdatadb;

CREATE USER frontenddb;
ALTER USER frontenddb WITH PASSWORD 'passwd3';
CREATE DATABASE frontend OWNER frontenddb;
GRANT ALL PRIVILEGES ON DATABASE frontend TO frontenddb;
