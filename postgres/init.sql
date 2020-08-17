-- DO NOT DEFINE THE PASSWORDS LIKE THIS IN PRODUCTION
CREATE USER userdb;
ALTER USER userdb WITH PASSWORD 'passwd1';
CREATE DATABASE users;
GRANT ALL PRIVILEGES ON DATABASE users TO userdb;

CREATE USER weatherdatadb;
ALTER USER weatherdatadb WITH PASSWORD 'passwd2';
CREATE DATABASE weatherdata;
GRANT ALL PRIVILEGES ON DATABASE weatherdata TO weatherdatadb;
