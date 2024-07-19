import boto3
import jsot boto3
import json
import psycopg2
from psycopg2.extras import execute_values
# AWS Lambda function handler
def lambda_handler(event, context):
    # Initialize AWS clients
    s3 = boto3.client('s3')
    db = psycopg2.connect(
        dbname='your_database_name',
        user='your_database_username',
        password='your_database_password',
        host='your_database_host',
        port='your_database_port'
    )
    cursor = db.cursor()
    # Retrieve JSON data from S3 bucket
    bucket_name = 'your_s3_bucket_name'
    file_name = 'your_file_name.json'
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    json_data = json.loads(response['Body'].read().decode('utf-8'))
    # Create tables in PostgreSQL database
    cursor.execute('''
        CREATE SCHEMA IF NOT EXISTS plants;
        CREATE TABLE IF NOT EXISTS plants.plants (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS plants.inverters (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS plants.batteries (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS plants.plant_inverters (
            plant_id INTEGER NOT NULL,
            inverter_id INTEGER NOT NULL,
            PRIMARY KEY (plant_id, inverter_id),
            FOREIGN KEY (plant_id) REFERENCES plants.plants (id),
            FOREIGN KEY (inverter_id) REFERENCES plants.inverters (id)
        );
        CREATE TABLE IF NOT EXISTS plants.inverter_batteries (
            inverter_id INTEGER NOT NULL,
            battery_id INTEGER NOT NULL,
            PRIMARY KEY (inverter_id, battery_id),
            FOREIGN KEY (inverter_id) REFERENCES plants.inverters (id),
            FOREIGN KEY (battery_id) REFERENCES plants.batteries (id)
        );
    ''')
    # Insert data into tables
    plants = []
    inverters = []
    batteries = []
    for plant in json_data['plants']:
        plants.append((plant['id'], plant['name']))
        for inverter in plant['inverters']:
            inverters.append((inverter['id'], inverter['name']))
            for battery in inverter['batteries']:
                batteries.append((battery['id'], battery['name']))
    execute_values(cursor, 'INSERT INTO plants.plants (id, name) VALUES %s', plants)
    execute_values(cursor, 'INSERT INTO plants.inverters (id, name) VALUES %s', inverters)
    execute_values(cursor, 'INSERT INTO plants.batteries (id, name) VALUES %s', batteries)
    for plant in json_data['plants']:
        for inverter in plant['inverters']:
            for battery in inverter['batteries']:
                execute_values(cursor, 'INSERT INTO plants.plant_inverters (plant_id, inverter_id) VALUES %s', [(plant['id'], inverter['id'])])
                execute_values(cursor, 'INSERT INTO plants.inverter_batteries (inverter_id, battery_id) VALUES %s', [(inverter['id'], battery['id'])])
    # Commit changes and close the database connection
    db.commit()
    cursor.close()
    db.close()
    # Return a success response
    return {
        'statusCode': 200,
        'statusMessage': 'JSON data imported successfully'
    }
