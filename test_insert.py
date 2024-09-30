# import requests
# import json
# import os
# from dotenv import load_dotenv
# import numpy as np

# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# # SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
# print(f"URL: {SUPABASE_URL}")
# print(f"API Key: {SUPABASE_KEY[:4]}")

# # Function to generate a random 384-dimensional embedding
# def generate_embedding():
#     return np.random.uniform(-0.1, 0.1, 384).tolist()

# def test_insert():
#     """Directly insert a simple row into Supabase using the REST API."""
#     try:
#         headers = {
#             "apikey": SUPABASE_KEY,  # The service role API key
#             "Authorization": f"Bearer {SUPABASE_KEY}",  # Bearer token is also the service role key
#             "Content-Type": "application/json"
#         }

#         data = {
#             "question_id": "df127952-5296-427e-aaed-bbca376539d5",  # Example UUID
#             "embedding": generate_embedding()  # Use the embedding function
#         }

#         response = requests.post(
#             f"{SUPABASE_URL}/rest/v1/embeddings",
#             headers=headers,
#             data=json.dumps(data)
#         )

#         response.raise_for_status()  # Raise an error for bad HTTP status codes
#         print(f"Supabase response: {response}")  # Log the raw response for debugging
#         # print(f"Supabase response: {response.json()}")  # Log the raw response for debugging

#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")
#     except Exception as e:
#         print(f"Error: {e}")
#         raise

# # Run the test insert
# test_insert()

import os
from dotenv import load_dotenv
import numpy as np
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions  # Import ClientOptions

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
print(f"URL: {SUPABASE_URL}")
print(f"API Key: {SUPABASE_KEY[:4]}")

# Initialize the Supabase client with the `vector` schema
client_options = ClientOptions(schema="vector")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=client_options)

# Function to generate a random 384-dimensional embedding
def generate_embedding():
    return np.random.uniform(-0.1, 0.1, 384).tolist()

def test_insert():
    """Insert a row into Supabase using the Python client with the 'vector' schema."""
    try:
        # Data to insert
        data = {
            "question_id": "df127952-6677-427e-aaed-bbca376539d5",  # Example UUID
            "embedding": generate_embedding()  # Use the embedding function
        }

        # Insert the data into the `vector.embeddings` table
        response = supabase.table("embeddings").insert(data).execute()

        # Log the response from Supabase
        print(f"Supabase response: {response.data}")  # Log the data for debugging

    except Exception as e:
        print(f"Error: {e}")
        raise

# Run the test insert
test_insert()
