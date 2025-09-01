from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments applied to all tasks
default_args = {
    'owner': 'aditya',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define Python functions for tasks
def print_hello():
    print("Hello World")

def print_time():
    print(f"Execution time: {datetime.now()}")

# Create DAG
with DAG(
    dag_id="hello_world_dag",
    default_args=default_args,
    description="A simple Hello World DAG",
    schedule="@daily",   # Runs once a day
    start_date=datetime(2025, 1, 1),
    catchup=False,                # Don't backfill old runs
    tags=["example", "hello"],
) as dag:

    # Tasks
    task_hello = PythonOperator(
        task_id="say_hello",
        python_callable=print_hello,
    )

    task_time = PythonOperator(
        task_id="print_execution_time",
        python_callable=print_time,
    )

    # Task order
    task_hello >> task_time