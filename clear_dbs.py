import os
import argparse
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from google_drive_auth import authenticate_google_drive
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from loguru import logger

# Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Neo4j Configuration
neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
# print(neo4j_password)
# print(neo4j_username)
# print(neo4j_uri)
# Google Drive Authentication
service = authenticate_google_drive()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# print(SUPABASE_URL)

# Initialize the Supabase client with the `vector` schema
client_options = ClientOptions(schema="vector")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=client_options)

def delete_all_embeddings():
    """Deletes all rows from the vector.embeddings table."""
    try:
        logger.info("Deleting all rows from Supabase vector.embeddings table...")
        response = supabase.table("embeddings").delete().neq('question_id', '6f8b39d6-4f6f-4e22-8e6d-abcde1234567').execute() # check against valid random uuid
        logger.info(f"Deleted rows: {response.data}")
    except Exception as e:
        logger.error(f"Error deleting embeddings: {e}")
        raise

# Neo4j Cleanup
def cleanup_neo4j():
    """Deletes all nodes, relationships, and vector indexes related to Question, Body, Tag, and Topic."""
    try:
        logger.info("Cleaning up Neo4j database...")
        with driver.session() as session:
            # Delete nodes and relationships
            session.run("MATCH (n) WHERE n:Question OR n:Body OR n:Tag OR n:Topic DETACH DELETE n")
            logger.info("Nodes and relationships deleted.")

            # Drop vector indexes (specify any vector indexes you know exist)
            index_result = session.run("SHOW INDEXES WHERE type = 'VECTOR'")
            for record in index_result:
                index_name = record['name']
                session.run(f"DROP INDEX {index_name}")
                logger.info(f"Vector index '{index_name}' deleted.")

        logger.info("Neo4j database cleaned successfully.")
    except Exception as e:
        logger.error(f"Error cleaning Neo4j database: {e}")
        raise


# Get or create 'carnivore' folder in Google Drive
def get_or_create_carnivore_folder(service):
    """Get the 'carnivore' folder ID, or create it if it doesn't exist."""
    query = "name = 'carnivore' and mimeType = 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    else:
        file_metadata = {'name': 'carnivore', 'mimeType': 'application/vnd.google-apps.folder'}
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

# Google Drive Cleanup
def cleanup_google_drive(service):
    """Deletes files from Google Drive inside the 'carnivore' folder that are tagged as 'api-generated'."""
    try:
        folder_id = get_or_create_carnivore_folder(service)
        query = f"'{folder_id}' in parents and fullText contains 'api-generated'"
        results = service.files().list(q=query, fields="files(id, name)").execute()

        files_to_delete = results.get('files', [])
        if not files_to_delete:
            logger.info("No 'api-generated' files found in the 'carnivore' folder to delete.")
            return

        for file in files_to_delete:
            logger.info(f"Deleting file: {file['name']} (ID: {file['id']})")
            service.files().delete(fileId=file['id']).execute()

        logger.info("Google Drive cleaned successfully.")
    except Exception as e:
        logger.error(f"Error cleaning Google Drive: {e}")
        raise

# Main cleanup function
def main(args):
    if args.supabase or args.all:
        delete_all_embeddings()

    if args.neo4j or args.all:
        cleanup_neo4j()

    if args.google_drive or args.all:
        cleanup_google_drive(service)

if __name__ == "__main__":
    # Define argument parser
    parser = argparse.ArgumentParser(description="Clean various data stores.")
    parser.add_argument("--supabase", action="store_true", help="Clean the Supabase vector.embeddings table")
    parser.add_argument("--neo4j", action="store_true", help="Clean the Neo4j database")
    parser.add_argument("--google_drive", action="store_true", help="Clean the Google Drive 'carnivore' folder")
    parser.add_argument("--all", "-a", action="store_true", help="Clean everything (Supabase, Neo4j, Google Drive)")

    # Parse the arguments
    args = parser.parse_args()

    # Run the main function with the provided arguments
    main(args)





# import os
# from neo4j import GraphDatabase
# from dotenv import load_dotenv
# from google_drive_auth import authenticate_google_drive
# from supabase import create_client, Client
# from supabase.lib.client_options import ClientOptions 

# load_dotenv()

# # Neo4j Configuration
# neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
# neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
# neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")
# driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

# # Google Drive Authentication
# service = authenticate_google_drive()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# # Initialize the Supabase client with the `vector` schema
# client_options = ClientOptions(schema="vector")
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=client_options)

# def delete_all_embeddings():
#     """Deletes all rows from the vector.embeddings table."""
#     try:
#         # Delete all records from the table without any condition
#         response = supabase.table("embeddings").delete().neq("question_id", "df127952-6776-427e-aaed-bbca376539d5").execute()


#         # Log the response from Supabase
#         print(f"Deleted rows: {response.data}")  # Log the data for debugging

#     except Exception as e:
#         print(f"Error: {e}")
#         raise




# # Neo4j Cleanup
# def cleanup_neo4j():
#     """Deletes all nodes and relationships related to Question, Body, Tag, and Topic."""
#     with driver.session() as session:
#         session.run("MATCH (n) WHERE n:Question OR n:Body OR n:Tag OR n:Topic DETACH DELETE n")

# # Get or create 'carnivore' folder in Google Drive
# def get_or_create_carnivore_folder(service):
#     """Get the 'carnivore' folder ID, or create it if it doesn't exist."""
#     # Search for the 'carnivore' folder in Google Drive
#     query = "name = 'carnivore' and mimeType = 'application/vnd.google-apps.folder'"
#     results = service.files().list(q=query, fields="files(id, name)").execute()
#     folders = results.get('files', [])
    
#     if folders:
#         # Folder exists, return its ID
#         return folders[0]['id']
#     else:
#         # Create the 'carnivore' folder
#         file_metadata = {
#             'name': 'carnivore',
#             'mimeType': 'application/vnd.google-apps.folder'
#         }
#         folder = service.files().create(body=file_metadata, fields='id').execute()
#         return folder.get('id')

# # Google Drive Cleanup
# def cleanup_google_drive(service):
#     """Deletes files from Google Drive inside the 'carnivore' folder that are tagged as 'api-generated'."""
#     # Get the 'carnivore' folder ID
#     folder_id = get_or_create_carnivore_folder(service)

#     # Search for files in the 'carnivore' folder and that contain 'api-generated' in their full text
#     query = f"'{folder_id}' in parents and fullText contains 'api-generated'"
#     results = service.files().list(q=query, fields="files(id, name)").execute()

#     files_to_delete = results.get('files', [])
    
#     if not files_to_delete:
#         print("No 'api-generated' files found in the 'carnivore' folder to delete.")
#         return

#     for file in files_to_delete:
#         print(f"Deleting file: {file['name']} (ID: {file['id']})")
#         service.files().delete(fileId=file['id']).execute()

# # Main cleanup function
# def main():
#     # Clean up Neo4j database
#     cleanup_neo4j()

#     # Clean up Google Drive API-generated files in the 'carnivore' folder
#     cleanup_google_drive(service)

#     # Run the delete function
#     delete_all_embeddings()

# if __name__ == "__main__":
#     main()
