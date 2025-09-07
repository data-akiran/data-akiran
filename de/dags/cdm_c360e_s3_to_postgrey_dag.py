from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import requests
import os

# Fixed S3 URL format
S3_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
LOCAL_FILE = "/tmp/yellow_tripdata.parquet"

def extract_from_s3():
    r = requests.get(S3_URL, stream=True)
    with open(LOCAL_FILE, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)

def transform_data():
    # Read parquet file instead of CSV
    df = pd.read_parquet(LOCAL_FILE)
    df = df.head(1000)  # Limit rows after reading
    # simple transform: keep only pickup/dropoff datetime + fare
    df = df[["tpep_pickup_datetime", "tpep_dropoff_datetime", "fare_amount"]]
    # Save as CSV for easier loading to Postgres
    csv_file = "/tmp/yellow_tripdata.csv"
    df.to_csv(csv_file, index=False)
    return csv_file

def load_to_postgres():
    import psycopg2
    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres",   # service name from docker-compose
        port=5432
    )
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nyc_taxi (
            pickup TIMESTAMP,
            dropoff TIMESTAMP,
            fare NUMERIC
        )
    """)
    conn.commit()

    # Load CSV into Postgres
    csv_file = "/tmp/yellow_tripdata.csv"
    with open(csv_file, "r") as f:
        next(f)  # skip header
        cur.copy_from(f, "nyc_taxi", sep=",")
    conn.commit()
    cur.close()
    conn.close()


with DAG(
    dag_id="cdm_c360e_s3_to_postgres_dag",
    start_date=datetime(2023, 1, 1),
    schedule=None,   # run manually
    catchup=False,
    tags=["example", "etl"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_from_s3",
        python_callable=extract_from_s3,
    )

    transform_task = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data,
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres,
    )

    extract_task >> transform_task >> load_task