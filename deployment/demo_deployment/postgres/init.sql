/*
 * Remote Weather Access - Client/server solution for distributed weather networks
 *  Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
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
CREATE USER userdb;
ALTER USER userdb WITH PASSWORD 'passwd1';
CREATE DATABASE users;
GRANT ALL PRIVILEGES ON DATABASE users TO userdb;

CREATE USER weatherdatadb;
ALTER USER weatherdatadb WITH PASSWORD 'passwd2';
CREATE DATABASE weatherdata;
GRANT ALL PRIVILEGES ON DATABASE weatherdata TO weatherdatadb;
