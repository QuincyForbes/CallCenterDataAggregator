import logging
from clickhouse_driver import Client
from faker import Faker
import uuid
import random
import os
from datetime import timedelta

# ClickHouse connection
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE")
CLICKHOUSE_TABLE = os.getenv("CLICKHOUSE_TABLE")


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ClickHouse connection
try:
    client = Client(
        host=CLICKHOUSE_HOST,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        port=CLICKHOUSE_PORT,
    )
except Exception as e:
    logging.error(f"Error connecting to ClickHouse: {e}")
    raise

# Check if database exists, if not create it
db_name = CLICKHOUSE_DATABASE
try:
    databases = client.execute("SHOW DATABASES")
    if db_name not in [db[0] for db in databases]:
        client.execute(f"CREATE DATABASE {db_name}")
except Exception as e:
    logging.error(f"Error checking/creating database: {e}")
    raise

# Check if table exists, if not create it
table_name = CLICKHOUSE_TABLE
try:
    tables = client.execute(f"SHOW TABLES FROM {db_name}")
    if table_name not in [table[0] for table in tables]:
        client.execute(
            f"""
            CREATE TABLE {db_name}.{table_name} (
                customer_id String,
                conversation_id String,
                agent_id String,
                call_start DateTime,
                call_end DateTime,
                call_duration_sec Int32,
                call_status String,
                transcript String,
                sentiment_score Float64,
                keywords Array(String)
            ) ENGINE = MergeTree()
            ORDER BY (agent_id, call_start)
        """
        )
except Exception as e:
    logging.error(f"Error checking/creating table: {e}")
    raise

# Fetch existing agent_ids
try:
    agent_ids = [
        row[0]
        for row in client.execute(
            f"SELECT DISTINCT agent_id FROM {db_name}.{table_name}"
        )
    ]
    if len(agent_ids) < 5:
        num_new_ids = 5 - len(agent_ids)
        logging.info(f"Less than 5 agent_ids found in the database. Generating {num_new_ids} new agent_ids.")
        new_agent_ids = [str(uuid.uuid4()) for _ in range(num_new_ids)]
        agent_ids.extend(new_agent_ids)
except Exception as e:
    logging.error(f"Error fetching agent_ids: {e}")
    raise


# Generate fake data
fake = Faker()
call_statuses = ["Answered", "Missed", "Rejected", "Hangup", "Voicemail"]
for agent_id in agent_ids:
    for i in range(7):  # Generate 5 entries for each agent ID
        try:
            call_start = fake.date_time_between(start_date="-1d", end_date="now")
            call_end = call_start + timedelta(seconds=random.randint(10, 3600))
            call_duration = (call_end - call_start).seconds

            client.execute(
                f"""
                INSERT INTO {db_name}.{table_name} (
                    customer_id,
                    conversation_id,
                    agent_id,
                    call_start,
                    call_end,
                    call_duration_sec,
                    call_status,
                    transcript,
                    sentiment_score,
                    keywords
                ) VALUES (
                    %(customer_id)s,
                    %(conversation_id)s,
                    %(agent_id)s,
                    %(call_start)s,
                    %(call_end)s,
                    %(call_duration)s,
                    %(call_status)s,
                    %(transcript)s,
                    %(sentiment_score)s,
                    %(keywords)s
                )
                """,
                {
                    "customer_id": str(uuid.uuid4()),
                    "conversation_id": str(uuid.uuid4()),
                    "agent_id": agent_id,  # Use the current agent ID
                    "call_start": call_start,
                    "call_end": call_end,
                    "call_duration": call_duration,
                    "call_status": random.choice(call_statuses),
                    "transcript": fake.text(),
                    "sentiment_score": random.uniform(-1.0, 1.0),
                    "keywords": [fake.word() for _ in range(random.randint(1, 5))],
                },
            )
            logging.info(f"Inserted entry {i + 1} for agent {agent_id}")
        except Exception as e:
            logging.error(f"Error inserting entry {i + 1} for agent {agent_id}: {e}")
            raise

logging.info("Data generation complete.")


# def reset(client, database_name, table_name):
#     """
#     Drops the specified database and table in the ClickHouse server.

#     Parameters:
#         client (clickhouse_driver.Client): A ClickHouse client instance.
#         database_name (str): The name of the database to be dropped.
#         table_name (str): The name of the table to be dropped.

#     Returns:
#         None
#     """
#     # Check if the database exists
#     databases = client.execute("SHOW DATABASES")
#     if database_name in [db[0] for db in databases]:
#         # Check if the table exists in the database
#         tables = client.execute(f"SHOW TABLES IN {database_name}")
#         if table_name in [table[0] for table in tables]:
#             # If the table exists, drop the table
#             try:
#                 client.execute(f"DROP TABLE {database_name}.{table_name}")
#                 logging.info(
#                     f'Dropped table "{table_name}" in database "{database_name}"'
#                 )
#             except Exception as e:
#                 logging.error(
#                     f"Error dropping table {table_name} in database {database_name}: {e}"
#                 )
#                 raise

#         # After checking and dropping table, drop the database
#         try:
#             client.execute(f"DROP DATABASE {database_name}")
#             logging.info(f'Dropped database "{database_name}"')
#         except Exception as e:
#             logging.error(f"Error dropping database {database_name}: {e}")
#             raise
#     else:
#         logging.info(f'Database "{database_name}" does not exist')


# client = Client(host=host, user=user, password=password, port=port)
# reset(client, "testdata", "conversations")
