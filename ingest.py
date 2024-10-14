import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from google_drive_auth import authenticate_google_drive
from googleapiclient.http import MediaFileUpload
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger
from neo4j_graphrag.indexes import create_vector_index, upsert_vector

# Load environment variables
load_dotenv()


# Google Drive Authentication
service = authenticate_google_drive()
google_drive_folder_id = "1pyAQY1UpjoR1vjCAUv3r_dCeUnxSGPSK"
# google_drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Neo4j Configuration
neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

# Connect to the Neo4j database
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
logger.info("Neo4j driver initialized")

# Hugging Face Embeddings Model
embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
logger.info("Hugging Face Embeddings model loaded")

# Function to delete the existing vector index if it exists
def delete_vector_index(driver, custom_index_name):
    """Delete a vector index if it exists."""
    with driver.session() as session:
        # Find the actual name of the index based on its custom name
        result = session.run("SHOW INDEXES YIELD name, entityType WHERE entityType = 'NODE' RETURN name")
        indexes = result.values()

        # Loop through the indexes to find the custom index name
        for index_record in indexes:
            index_name = index_record[0]
            if custom_index_name in index_name:
                session.run(f"DROP INDEX {index_name}")
                logger.info(f"Vector index '{index_name}' deleted successfully.")
                return
        logger.info(f"Vector index '{custom_index_name}' does not exist, skipping deletion.")




def create_vector_index(driver, index_name, label, embedding_property, dimensions, similarity_fn):
    """Create a vector index with Neo4j using cosine similarity."""
    with driver.session() as session:
        session.run(
            f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON (n.{embedding_property})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimensions},
                    `vector.similarity_function`: '{similarity_fn}' 
                }}
            }}
            """
        )
        logger.info(f"Vector index '{index_name}' created successfully.")

# Now pass "cosine" as the similarity function instead of "euclidean"
create_vector_index(
    driver=driver,
    index_name="carnivore1",
    label="Question",
    embedding_property="embedding",
    dimensions=384,  # Adjust this based on your embedding model
    similarity_fn="cosine"  # Change from "euclidean" to "cosine"
)


def load_json(file_path):
    """Loads the JSON file."""
    logger.info(f"Loading JSON file from {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)
    
def get_or_create_carnivore_folder(service):
    """Retrieve the folder ID from the environment and return it."""
    if google_drive_folder_id:
        logger.info(f"Using folder ID from environment: {google_drive_folder_id}")
        return google_drive_folder_id
    else:
        logger.error("No Google Drive folder ID found in the environment.")
        raise ValueError("Google Drive folder ID not found in environment.")

# def get_or_create_carnivore_folder(service):
#     """Get the 'carnivore' folder ID, or create it if it doesn't exist."""
#     logger.info("Searching for 'carnivore' folder in Google Drive")
#     query = "name = 'carnivore' and mimeType = 'application/vnd.google-apps.folder'"
#     results = service.files().list(q=query, fields="files(id, name)").execute()
#     folders = results.get('files', [])
    
#     if folders:
#         folder_id = folders[0]['id']
#         logger.info(f"Found existing 'carnivore' folder with ID: {folder_id}")
#         return folder_id
#     else:
#         logger.info("Creating 'carnivore' folder in Google Drive")
#         file_metadata = {
#             'name': 'carnivore',
#             'mimeType': 'application/vnd.google-apps.folder'
#         }
#         folder = service.files().create(body=file_metadata, fields='id').execute()
#         folder_id = folder.get('id')
#         logger.info(f"Created 'carnivore' folder with ID: {folder_id}")
#         return folder_id

def upload_to_drive(service, file_name, text_content):
    """Uploads the given text to Google Drive inside the 'carnivore' folder and tags it as 'api-generated'."""
    logger.info(f"Uploading {file_name} to Google Drive")
    folder_id = get_or_create_carnivore_folder(service)

    # Save the content to a temporary file
    temp_file_path = f'/tmp/{file_name}.txt'
    with open(temp_file_path, 'w') as f:
        f.write(text_content)
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id],
        'mimeType': 'text/plain',
        'description': 'api-generated'
    }
    
    media = MediaFileUpload(temp_file_path, mimetype='text/plain')
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    file_id = uploaded_file.get('id')
    logger.info(f"File {file_name} uploaded with ID: {file_id}")

    # Make the file publicly accessible
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
    
    shareable_link = f"https://drive.google.com/uc?id={file_id}"
    logger.info(f"Shareable link for {file_name}: {shareable_link}")
    return shareable_link

def generate_embedding(text):
    """Generates an embedding for the given text."""
    logger.info(f"Generating embedding for text: {text[:50]}...")
    embedding = embed_model.embed_documents([text])[0]
    logger.info(f"Generated embedding of length: {len(embedding)}")
    return embedding



def add_data_to_neo4j(question_data, service):
    with driver.session() as session:
        for index, question in enumerate(question_data):
            try:
                logger.info(f"Processing question {index + 1}/{len(question_data)}: {question['question'][:50]}...")

                # Add Question Node in Neo4j without the date field
                result = session.run(
                    """
                    CREATE (q:Question {id: randomUUID(), title: $title, text: $text}) 
                    RETURN q.id AS question_id
                    """, title=question['title'], text=question['question']
                )
                question_id = result.single()['question_id']
                logger.info(f"Question added with ID: {question_id}")

                # Generate embedding for the question text
                embedding = generate_embedding(question['question'])

                # Upsert the embedding into the Question node
                session.run(
                    """
                    MATCH (q:Question {id: $question_id})
                    SET q.embedding = $embedding
                    """, question_id=question_id, embedding=embedding
                )
                logger.info(f"Embedding added to Question ID: {question_id}")

                # Continue with processing body, tags, etc.
                body = question['body']
                file_name = f"body_text_{index+1}"  # Using index as a placeholder for date
                drive_link = upload_to_drive(service, file_name, body)
                logger.info(f"Uploaded body text to Google Drive with link: {drive_link}")

                # Add Body Node with reference to Google Drive text
                session.run(
                    "CREATE (b:Body {id: randomUUID(), text_link: $text_link})",
                    text_link=drive_link
                )
                logger.info(f"Body added with Google Drive link: {drive_link}")

                # Create the HAS_BODY relationship
                session.run(
                    """
                    MATCH (q:Question {id: $qid}), (b:Body {text_link: $btext_link})
                    CREATE (q)-[:HAS_BODY]->(b)
                    """, qid=question_id, btext_link=drive_link
                )
                logger.info(f"Created HAS_BODY relationship for Question ID: {question_id}")

                # Add Tags to the Body Node if they exist
                if 'tags' in question:
                    for tag in question['tags']:
                        session.run(
                            """
                            MERGE (t:Tag {word: $word})
                            WITH t
                            MATCH (b:Body {text_link: $btext_link})
                            MERGE (b)-[:HAS_TAG]->(t)
                            """, word=tag, btext_link=drive_link
                        )
                        logger.info(f"Tag {tag} added to Body with link: {drive_link}")

            except Exception as e:
                logger.error(f"Error processing question {index + 1}: {e}")
                continue



def main():
    file_path = "new_data_structure/second_ingest_data.json"
    data = load_json(file_path)

    num_questions = len(data)
    logger.info(f"Loaded {num_questions} questions from {file_path}")

    add_data_to_neo4j(data, service)
    logger.info("Data ingestion completed")

if __name__ == "__main__":
    main()







# import os
# import json
# from neo4j import GraphDatabase
# from dotenv import load_dotenv
# from google_drive_auth import authenticate_google_drive
# from googleapiclient.http import MediaFileUpload
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from loguru import logger
# from neo4j_graphrag.indexes import create_vector_index, upsert_vector

# # Load environment variables
# load_dotenv()

# # Google Drive Authentication
# service = authenticate_google_drive()

# # Neo4j Configuration
# neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
# neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
# neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

# # Connect to the Neo4j database
# driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
# logger.info("Neo4j driver initialized")

# # Hugging Face Embeddings Model
# embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# logger.info("Hugging Face Embeddings model loaded")

# # Create Vector Index
# INDEX_NAME = "question-vector-index"
# create_vector_index(
#     driver,
#     INDEX_NAME,
#     label="Question",
#     embedding_property="embedding",
#     dimensions=384,  # Adjust to match your embedding model dimensions
#     similarity_fn="euclidean"
# )
# logger.info(f"Vector index '{INDEX_NAME}' created")

# def load_json(file_path):
#     """Loads the JSON file."""
#     logger.info(f"Loading JSON file from {file_path}")
#     with open(file_path, 'r') as f:
#         return json.load(f)

# def get_or_create_carnivore_folder(service):
#     """Get the 'carnivore' folder ID, or create it if it doesn't exist."""
#     logger.info("Searching for 'carnivore' folder in Google Drive")
#     query = "name = 'carnivore' and mimeType = 'application/vnd.google-apps.folder'"
#     results = service.files().list(q=query, fields="files(id, name)").execute()
#     folders = results.get('files', [])
    
#     if folders:
#         folder_id = folders[0]['id']
#         logger.info(f"Found existing 'carnivore' folder with ID: {folder_id}")
#         return folder_id
#     else:
#         logger.info("Creating 'carnivore' folder in Google Drive")
#         file_metadata = {
#             'name': 'carnivore',
#             'mimeType': 'application/vnd.google-apps.folder'
#         }
#         folder = service.files().create(body=file_metadata, fields='id').execute()
#         folder_id = folder.get('id')
#         logger.info(f"Created 'carnivore' folder with ID: {folder_id}")
#         return folder_id

# def upload_to_drive(service, file_name, text_content):
#     """Uploads the given text to Google Drive inside the 'carnivore' folder and tags it as 'api-generated'."""
#     logger.info(f"Uploading {file_name} to Google Drive")
#     folder_id = get_or_create_carnivore_folder(service)

#     # Save the content to a temporary file
#     temp_file_path = f'/tmp/{file_name}.txt'
#     with open(temp_file_path, 'w') as f:
#         f.write(text_content)
    
#     file_metadata = {
#         'name': file_name,
#         'parents': [folder_id],
#         'mimeType': 'text/plain',
#         'description': 'api-generated'
#     }
    
#     media = MediaFileUpload(temp_file_path, mimetype='text/plain')
#     uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
#     file_id = uploaded_file.get('id')
#     logger.info(f"File {file_name} uploaded with ID: {file_id}")

#     # Make the file publicly accessible
#     service.permissions().create(
#         fileId=file_id,
#         body={'type': 'anyone', 'role': 'reader'}
#     ).execute()
    
#     shareable_link = f"https://drive.google.com/uc?id={file_id}"
#     logger.info(f"Shareable link for {file_name}: {shareable_link}")
#     return shareable_link

# def generate_embedding(text):
#     """Generates an embedding for the given text."""
#     logger.info(f"Generating embedding for text: {text[:50]}...")
#     embedding = embed_model.embed_documents([text])[0]
#     logger.info(f"Generated embedding of length: {len(embedding)}")
#     return embedding

# def add_data_to_neo4j(question_data, service):
#     with driver.session() as session:
#         for index, question in enumerate(question_data):
#             try:
#                 logger.info(f"Processing question {index + 1}/{len(question_data)}: {question['question'][:50]}...")

#                 # Add Question Node in Neo4j and retrieve the generated question_id
#                 result = session.run(
#                     """
#                     CREATE (q:Question {id: randomUUID(), title: $title, text: $text, date: $date}) 
#                     RETURN q.id AS question_id
#                     """, title=question['title'], text=question['question'], date=question['date']
#                 )
#                 question_id = result.single()['question_id']
#                 logger.info(f"Question added with ID: {question_id}")

#                 # Generate embedding for the question text
#                 embedding = generate_embedding(question['question'])

#                 # Upsert the embedding into the vector index
#                 upsert_vector(driver, node_id=question_id, embedding_property="embedding", vector=embedding)
#                 logger.info(f"Embedding added to Question ID: {question_id} in the vector index")

#                 # Process body and store it in Google Drive
#                 body = question['body']
#                 file_name = f"body_text_{question['date']}"
#                 drive_link = upload_to_drive(service, file_name, body)
#                 logger.info(f"Uploaded body text to Google Drive with link: {drive_link}")

#                 # Add Body Node with reference to Google Drive text
#                 session.run(
#                     "CREATE (b:Body {id: randomUUID(), text_link: $text_link, date: $date})",
#                     text_link=drive_link, date=question['date']
#                 )
#                 logger.info(f"Body added with Google Drive link: {drive_link}")

#                 # Create the HAS_BODY relationship
#                 session.run(
#                     """
#                     MATCH (q:Question {id: $qid}), (b:Body {text_link: $btext_link})
#                     CREATE (q)-[:HAS_BODY]->(b)
#                     """, qid=question_id, btext_link=drive_link
#                 )
#                 logger.info(f"Created HAS_BODY relationship for Question ID: {question_id}")

#                 # Add Tags to the Body Node
#                 if 'tags' in question:
#                     for tag in question['tags']:
#                         session.run(
#                             """
#                             MERGE (t:Tag {word: $word})
#                             WITH t
#                             MATCH (b:Body {text_link: $btext_link})
#                             MERGE (b)-[:HAS_TAG]->(t)
#                             """, word=tag, btext_link=drive_link
#                         )
#                         logger.info(f"Tag {tag} added to Body with link: {drive_link}")

#             except Exception as e:
#                 logger.error(f"Error processing question {index + 1}: {e}")
#                 continue

# def main():
#     file_path = "new_data_structure/ingest_data.json"
#     data = load_json(file_path)

#     num_questions = len(data)
#     logger.info(f"Loaded {num_questions} questions from {file_path}")

#     add_data_to_neo4j(data, service)
#     logger.info("Data ingestion completed")

# if __name__ == "__main__":
#     main()


# import os
# import json
# import logging
# from neo4j import GraphDatabase
# from dotenv import load_dotenv
# from google_drive_auth import authenticate_google_drive
# from googleapiclient.http import MediaFileUpload
# import supabase
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from supabase.lib.client_options import ClientOptions  # Updated import
# from loguru import logger
# from neo4j_graphrag.indexes import create_vector_index, upsert_vector

# # Load environment variables
# load_dotenv()

# # Google Drive Authentication
# service = authenticate_google_drive()

# # Supabase Configuration
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# client_options = ClientOptions(schema="vector")
# client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY, options=client_options)
# logger.info(f"Supabase URL: {SUPABASE_URL}")
# logger.info(f"Supabase Client initialized")

# # Neo4j Configuration
# neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
# neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
# neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

# # Connect to the Neo4j database
# driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
# logger.info("Neo4j driver initialized")

# # Hugging Face Embeddings Model
# embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# logger.info("Hugging Face Embeddings model loaded")

# # Create Vector Index
# INDEX_NAME = "question-vector-index"
# create_vector_index(
#     driver,
#     INDEX_NAME,
#     label="Question",
#     embedding_property="embedding",
#     dimensions=384,  # Adjust to match your embedding model dimensions
#     similarity_fn="euclidean"
# )
# logger.info(f"Vector index '{INDEX_NAME}' created")

# def load_json(file_path):
#     """Loads the JSON file."""
#     logger.info(f"Loading JSON file from {file_path}")
#     with open(file_path, 'r') as f:
#         return json.load(f)

# def get_or_create_carnivore_folder(service):
#     """Get the 'carnivore' folder ID, or create it if it doesn't exist."""
#     logger.info("Searching for 'carnivore' folder in Google Drive")
#     query = "name = 'carnivore' and mimeType = 'application/vnd.google-apps.folder'"
#     results = service.files().list(q=query, fields="files(id, name)").execute()
#     folders = results.get('files', [])
    
#     if folders:
#         folder_id = folders[0]['id']
#         logger.info(f"Found existing 'carnivore' folder with ID: {folder_id}")
#         return folder_id
#     else:
#         logger.info("Creating 'carnivore' folder in Google Drive")
#         file_metadata = {
#             'name': 'carnivore',
#             'mimeType': 'application/vnd.google-apps.folder'
#         }
#         folder = service.files().create(body=file_metadata, fields='id').execute()
#         folder_id = folder.get('id')
#         logger.info(f"Created 'carnivore' folder with ID: {folder_id}")
#         return folder_id

# def upload_to_drive(service, file_name, text_content):
#     """Uploads the given text to Google Drive inside the 'carnivore' folder and tags it as 'api-generated'."""
#     logger.info(f"Uploading {file_name} to Google Drive")
#     folder_id = get_or_create_carnivore_folder(service)

#     # Save the content to a temporary file
#     temp_file_path = f'/tmp/{file_name}.txt'
#     with open(temp_file_path, 'w') as f:
#         f.write(text_content)
    
#     file_metadata = {
#         'name': file_name,
#         'parents': [folder_id],
#         'mimeType': 'text/plain',
#         'description': 'api-generated'
#     }
    
#     media = MediaFileUpload(temp_file_path, mimetype='text/plain')
#     uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
#     file_id = uploaded_file.get('id')
#     logger.info(f"File {file_name} uploaded with ID: {file_id}")

#     # Make the file publicly accessible
#     service.permissions().create(
#         fileId=file_id,
#         body={'type': 'anyone', 'role': 'reader'}
#     ).execute()
    
#     shareable_link = f"https://drive.google.com/uc?id={file_id}"
#     logger.info(f"Shareable link for {file_name}: {shareable_link}")
#     return shareable_link

# def generate_embedding(text):
#     """Generates an embedding for the given text."""
#     logger.info(f"Generating embedding for text: {text[:50]}...")
#     embedding = embed_model.embed_documents([text])[0]
#     logger.info(f"Generated embedding of length: {len(embedding)}")
#     return embedding

# def add_data_to_neo4j(question_data, service):
#     with driver.session() as session:
#         for index, question in enumerate(question_data):
#             try:
#                 logger.info(f"Processing question {index + 1}/{len(question_data)}: {question['question'][:50]}...")

#                 # Add Question Node in Neo4j and retrieve the generated question_id
#                 result = session.run(
#                     """
#                     CREATE (q:Question {id: randomUUID(), text: $text, date: $date, topic: $topic}) 
#                     RETURN q.id AS question_id
#                     """, text=question['question'], date=question['date'], topic=question['topic']
#                 )
#                 question_id = result.single()['question_id']
#                 logger.info(f"Question added with ID: {question_id}")

#                 # Generate embedding for the question text
#                 embedding = generate_embedding(question['question'])

#                 # Upsert the embedding into the vector index
#                 upsert_vector(driver, node_id=question_id, embedding_property="embedding", vector=embedding)
#                 logger.info(f"Embedding added to Question ID: {question_id} in the vector index")

#                 # Process body and store it in Google Drive
#                 body = question['body']
#                 file_name = f"body_text_{question['date']}"
#                 drive_link = upload_to_drive(service, file_name, body['text'])
#                 logger.info(f"Uploaded body text to Google Drive with link: {drive_link}")

#                 # Add Body Node with reference to Google Drive text
#                 session.run(
#                     "CREATE (b:Body {id: randomUUID(), text_link: $text_link, date: $date})",
#                     text_link=drive_link, date=body['date']
#                 )
#                 logger.info(f"Body added with Google Drive link: {drive_link}")

#                 # Create the HAS_BODY relationship
#                 session.run(
#                     """
#                     MATCH (q:Question {id: $qid}), (b:Body {text_link: $btext_link})
#                     CREATE (q)-[:HAS_BODY]->(b)
#                     """, qid=question_id, btext_link=drive_link
#                 )
#                 logger.info(f"Created HAS_BODY relationship for Question ID: {question_id}")

#                 # Add Topic Node and Relationship (if a topic exists)
#                 if 'topic' in question:
#                     session.run(
#                         """
#                         MERGE (t:Topic {name: $topic})
#                         WITH t
#                         MATCH (q:Question {id: $qid})
#                         MERGE (q)-[:HAS_TOPIC]->(t)
#                         """, topic=question['topic'], qid=question_id
#                     )
#                     logger.info(f"Added Topic relationship for Question ID: {question_id} and Topic: {question['topic']}")

#                 # Add Tags to the Body Node
#                 if 'tags' in body:
#                     for tag in body['tags']:
#                         session.run(
#                             """
#                             MERGE (t:Tag {word: $word})
#                             WITH t
#                             MATCH (b:Body {text_link: $btext_link})
#                             MERGE (b)-[:HAS_TAG]->(t)
#                             """, word=tag, btext_link=drive_link
#                         )
#                         logger.info(f"Tag {tag} added to Body with link: {drive_link}")

#             except Exception as e:
#                 logger.error(f"Error processing question {index + 1}: {e}")
#                 continue

# def main():
#     file_path = "manually_cleaned_data/test_ingest_data/ingest_data.json"
#     data = load_json(file_path)

#     num_questions = len(data)
#     logger.info(f"Loaded {num_questions} questions from {file_path}")

#     add_data_to_neo4j(data, service)
#     logger.info("Data ingestion completed")

# if __name__ == "__main__":
#     main()
