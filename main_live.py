import os
import csv
import boto3
import datetime
import logging
import clickhouse_driver
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Get environment variables
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE")
CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_TABLE")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Retrieve conversation data from ClickHouse for a specific day
def retrieve_agent_metrics(clickhouse_client, date):
    try:
        query = f"""
        SELECT 
            agent_id, 
            avg(call_duration_sec) as average_call_length, 
            quantile(0.9)(call_duration_sec) as percentile_90_call_length
        FROM 
            {CLICKHOUSE_TABLE}
        WHERE 
            toDate(call_start) = '{date}'
        GROUP BY
            agent_id
        """
        result = clickhouse_client.execute(query)
        columns = ['agent_id', 'average_call_length', 'percentile_90_call_length']
        agent_metrics = [dict(zip(columns, row)) for row in result]
        return agent_metrics
    except Exception as e:
        logging.error(f"Error retrieving agent metrics: {e}")
        raise

# Generate a CSV file with the calculated metrics
def generate_csv_file(date, metrics):
    try:
        file_name = f"metrics_{date}.csv"
        with open(file_name, "w", newline="") as csv_file:
            fieldnames = ["agent_id", "average_call_length", "percentile_90_call_length"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for data in metrics:
                writer.writerow(data)

        return file_name
    except Exception as e:
        logging.error(f"Error generating CSV file: {e}")
        raise

# Upload a file to AWS S3
def upload_file_to_s3(file_path, s3_bucket):
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        with ThreadPoolExecutor() as executor:
            executor.submit(s3_client.upload_file, file_path, s3_bucket, os.path.basename(file_path))
    except Exception as e:
        logging.error(f"Error uploading file to S3: {e}")
        raise

# Entry point for the daily data export
def export_daily_metrics():
    try:
        clickhouse_client = clickhouse_driver.Client(
            host=CLICKHOUSE_HOST,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DATABASE,
            port=CLICKHOUSE_PORT,
        )

        # Assuming today's date for demonstration purposes
        today = datetime.date.today()
        agent_metrics = retrieve_agent_metrics(clickhouse_client, today)
        csv_file = generate_csv_file(today, agent_metrics)
        upload_file_to_s3(csv_file, S3_BUCKET_NAME)

        logging.info("Daily metrics export completed successfully.")
    except Exception as e:
        logging.error(f"Error in export_daily_metrics: {e}")
        raise

export_daily_metrics()
