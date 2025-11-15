-- sudo -u postgres psql
--- Apache Airflow
-- Create the database
CREATE DATABASE airflow_db ENCODING 'UTF8';

-- Create the user with a password
CREATE USER airflow_user WITH PASSWORD 'icc115';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;

-- The following commands are for demonstration purposes to show how to connect to the new DB
-- \c airflow_db;

-- You may also need to grant privileges on future tables and sequences in the database
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow_user;


--- RASA
CREATE DATABASE rasa_db ENCODING 'UTF8';

-- Create the user with a password
CREATE USER rasa_user WITH PASSWORD 'icc115';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE rasa_db TO rasa_user;

-- The following commands are for demonstration purposes to show how to connect to the new DB
-- \c rasa_db;

-- You may also need to grant privileges on future tables and sequences in the database
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rasa_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rasa_user;
-- \q