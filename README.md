# Project Outline

This project has been designed specifically to meet a unique customer request, which entails extracting relevant information on a daily basis from the 'conversations' table. This table stores comprehensive details about customer calls managed by various agents.

Table Structure
The 'conversations' table incorporates the following structure:

```
CREATE TABLE conversations
(
    customer_id UUID,
    conversation_id UUID,
    agent_id UUID,
    call_start DateTime,
    call_end DateTime,
    call_duration_sec Int32,
    call_status Enum8('Answered' = 1, 'Missed' = 2, 'Rejected' = 3, 'Hangup' = 4, 'Voicemail' = 5),
    transcript String,
    sentiment_score Float64,
    keywords Array(String),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (customer_id, agent_id, call_start);
```

## Customer Requirement

The customer mandate involves a daily data extraction process that computes the average call duration and the 90th percentile call length for each agent. These metrics will be compiled into a CSV file which will be subsequently uploaded into a designated AWS S3 bucket, generating one file every day.

## Proposed Solution

The proposed solution involves creating a Python script, set to run daily, which executes a SQL query to compute the requested statistics. The calculated data is then uploaded into the designated S3 bucket. GitHub Actions automate the daily execution.

## Implementation Steps

1. Configure the S3 Bucket.
2. Set up the AWS IAM User.
3. Assign access to the specific S3 Bucket to the AWS IAM User.
4. Create a ClickHouse Instance (EC2 Ubuntu - Free Tier).
5. Develop a Python script to generate data.
6. Create a Python script to aggregate data.
7. Conduct local testing of Python scripts.
8. Modify scripts to support variables and secrets from GitHub Actions. (This can be replaced with AWS Secrets Manager and a database for handling configurations for various clients).
9. Write a GitHub Action script to run the python scripts everyday at x time.
10. Test GitHub Actions.

## Scripts

generate_data_live: This script populates a ClickHouse database with synthetic call center data for testing or developmental purposes.

main_live.py: This script computes call center metrics (average and 90th percentile call length) and uploads the results to an S3 bucket.
Workflow

## Environment Variables

To effectively run these scripts, the following environment variables must be set:

```
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USER
CLICKHOUSE_PASSWORD
CLICKHOUSE_DATABASE
CLICKHOUSE_TABLE
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BUCKET_NAME
```

## Dependencies

```
boto3
clickhouse_driver
logging
faker
```

Ensure to install these dependencies using pip.

```
 pip install -r requirements.txt
```

## Usage

Presuming Python 3.x is installed and the required environment variables are set, you can directly execute each script using Python or the provided GitHub Actions:

```
generate_data_live.py
main_live.py
```

## Outcome

metrics_2023-07-14.csv
| agent_id | average_call_length | percentile_90_call_length |
|----------|---------------------|---------------------------|
| 066caa3c-b2f3-41be-8fbe-027f2a78cc33 | 2437 | 3248.9 |
| 68937efe-6a2e-4cf5-b690-8fb1a80efb7c | 1316.5 | 2680.3 |
| b7fb2d64-aad5-45a0-8cfb-151ee8ef2e5a | 1467.833333 | 2862 |
| daff7928-7911-42a0-a85f-3c4843e32428 | 1815.791045 | 3311.4 |
| 98074ae7-83fb-4531-a9f2-98ac6beefa4c | 1770.031746 | 3180.8 |

## Considerations

To monitor the status of this automation effectively, you might want to consider implementing a Prometheus exporter as a data source for Grafana. Additionally, setting up alerts and monitoring mechanisms could provide proactive oversight and ensure the system is functioning optimally.
If your metrics data is large, consider using pandas library which might write large data to CSV files faster than Python's built-in csv module.

## Note

The export_daily_metrics function uses the current day's date for demonstration purposes. In a production environment, this should be tailored to fit your specific requirements.
