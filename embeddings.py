from llama_index import (
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    LLMPredictor,
    ServiceContext,
    PromptHelper,
    StorageContext,
    load_index_from_storage
)
from llama_index.node_parser import SimpleNodeParser
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
import numpy as np
from dotenv import load_dotenv
import os


# Initialize the embedding model
embed_model = LangchainEmbedding(
    HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
)
def add_data_to_neo4j_with_embeddings(question_data):
    load_dotenv()

    neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
    neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
    neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

    # Connect to the Neo4j database
    uri = neo4j_uri
    username = neo4j_username
    password = neo4j_password

    driver = GraphDatabase.driver(uri, auth=(username, password))

    # Initialize embedding model
    embed_model = LangchainEmbedding(
        HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    )

    with driver.session() as session:
        for question in question_data:
            # Generate embedding for question text
            question_embedding = embed_model.embed(query_text=question['question'])

            # Add Question Node with embedding
            session.run(
                """
                CREATE (q:Question {
                    id: randomUUID(),
                    text: $text,
                    date: $date,
                    topic: $topic,
                    embedding: $embedding
                })
                """,
                text=question['question'],
                date=question['date'],
                topic=question.get('topic', ''),
                embedding=question_embedding
            )

            # Process Body Node
            body = question['body']

            # Generate embedding for body text
            body_embedding = embed_model.embed(query_text=body['text'])

            # Add Body Node with embedding
            session.run(
                """
                CREATE (b:Body {
                    id: randomUUID(),
                    text: $text,
                    date: $date,
                    embedding: $embedding
                })
                """,
                text=body['text'],
                date=body['date'],
                embedding=body_embedding
            )

            # Create the HAS_BODY relationship
            session.run(
                """
                MATCH (q:Question {text: $qtext}), (b:Body {text: $btext})
                CREATE (q)-[:HAS_BODY]->(b)
                """,
                qtext=question['question'], btext=body['text']
            )

            # Add Topic Node and Relationship (if a topic exists)
            if 'topic' in question:
                session.run(
                    """
                    MERGE (t:Topic {name: $topic})
                    WITH t
                    MATCH (q:Question {text: $qtext})
                    MERGE (q)-[:HAS_TOPIC]->(t)
                    """,
                    topic=question['topic'], qtext=question['question']
                )

            # Check if 'tags' exists in the body before trying to add them
            if 'tags' in body:
                for tag in body['tags']:
                    session.run(
                        """
                        MERGE (t:Tag {word: $word})
                        WITH t
                        MATCH (b:Body {text: $btext})
                        MERGE (b)-[:HAS_TAG]->(t)
                        """,
                        word=tag, btext=body['text']
                    )
