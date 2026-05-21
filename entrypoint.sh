#!/bin/bash
set -e

# Fix log directory permissions at container startup (runs as root)
mkdir -p /opt/airflow/logs/scheduler
chown -R airflow:root /opt/airflow/logs
chmod -R 775 /opt/airflow/logs

# Ensure airflow binary is on PATH when gosu drops to airflow user
export PATH=/home/airflow/.local/bin:$PATH

# Drop to airflow user and exec the command directly
exec gosu airflow "$@"