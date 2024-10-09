import boto3
import json
import requests
from requests.auth import HTTPBasicAuth
import os

s3_client = boto3.client('s3')

# OpenSearch details
OPENSEARCH_ENDPOINT = os.environ['https://search-weather-csrqxpvsrc6reiobwsynth57ji.aos.eu-north-1.on.aws/']  # OpenSearch domain endpoint
OPENSEARCH_USERNAME = os.environ['Ahmed']  # Username for basic auth
OPENSEARCH_PASSWORD = os.environ['AhmedM_1997']  # Password for basic auth
INDEX_NAME = 'weather_data'  # OpenSearch index name

def lambda_handler(event, context):
    for record in event['Records']:
        # Extract bucket and object details
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        object_size = record['s3']['object']['size']

        # Skip _spark_metadata and zero-size files
        if '_spark_metadata' in object_key or object_size == 0:
            print(f"Skipping file: {object_key} (either metadata or empty file)")
            continue
        
        # Determine city from the folder name
        city_name = get_city_name(object_key)

        # Download the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read().decode('utf-8')

        # Process the file content
        json_data = json.loads(file_content)

        # Add city_name to the data
        for record in json_data:
            record['city'] = city_name

        # Push the modified data to OpenSearch
        index_data_to_opensearch(json_data)

def get_city_name(object_key):
    if 'NewYork/' in object_key:
        return 'NewYork'
    elif 'SanFrancisco/' in object_key:
        return 'SanFrancisco'
    elif 'London/' in object_key:
        return 'London'
    else:
        return 'Unknown'

def index_data_to_opensearch(data):
    headers = {
        'Content-Type': 'application/json'
    }
    
    url = f"https://{OPENSEARCH_ENDPOINT}/{INDEX_NAME}/_bulk"
    
    # Prepare bulk indexing request
    bulk_data = ""
    for record in data:
        action_metadata = json.dumps({"index": {}})
        bulk_data += f"{action_metadata}\n"
        bulk_data += f"{json.dumps(record)}\n"
    
    # Perform the HTTP POST request to OpenSearch
    response = requests.post(
        url,
        data=bulk_data,
        headers=headers,
        auth=HTTPBasicAuth(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD)
    )
    
    # Log the response for debugging
    if response.status_code == 200:
        print("Data indexed successfully!")
    else:
        print(f"Failed to index data: {response.text}")

