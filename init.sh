sudo apt update
sudo apt install -y python3-pip python3-venv libpq-dev build-essential
# sudo apt install -y default-mysql-client default-libmysqlclient-dev pkg-config
python3 -m venv airflow_env
source airflow_env/bin/activate

sudo chown -R $(whoami):$(whoami) ~/apache-airflow/airflow-data
sudo chmod -R 755 ~/apache-airflow/airflow-data
sudo chmod u+x create-db-script.sql
export AIRFLOW_HOME=/home/icc115/apache-airflow/airflow-data
export AIRFLOW__SQL_ALCHEMY_CONN='postgresql+psycopg2://airflow_user:icc115@localhost:5432/airflow_db'
export AIRFLOW_VERSION=3.0.3

# sudo -u postgres psql

# Extract the version of Python you have installed. If you're currently using a Python version that is not supported by Airflow, you may want to set this manually.
# See above for supported versions.
export PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
# For example this would install 3.0.0 with python 3.10: https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.10.txt

pip install "apache-airflow[postgres]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
pip install apache-airflow-providers-postgres
