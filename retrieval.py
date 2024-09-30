import os
import logging
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import LLMInterface, LLMResponse
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger
from transformers import AutoModel, AutoTokenizer
import torch
import requests
from groq import Groq
from langchain_community.embeddings import HuggingFaceEmbeddings
from neo4j_graphrag.types import RetrieverResultItem

import json


# Load environment variables
load_dotenv()

INDEX_NAME = "question-vector-index"

# Neo4j Configuration
neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

groq_api_key = os.getenv("GROQ_API_KEY")
groq_model_name = "llama3-8b-8192"

# Connect to the Neo4j database
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
logger.info("Neo4j driver initialized")

# Hugging Face Embeddings Model (same model used for ingestion)
embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
logger.info("Hugging Face Embeddings model loaded")


class GroqLLM(LLMInterface):
    def __init__(self, model_name, api_key):
        self.model_name = model_name
        self.api_key = api_key
        # Initialize Groq client with API key
        self.client = Groq(api_key=self.api_key)

    def invoke(self, input: str) -> LLMResponse:
        """Invoke Groq's API synchronously using the Groq client."""
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": input
                }
            ],
            model=self.model_name
        )

        if response.choices:
            # Extract content from the response
            return LLMResponse(content=response.choices[0].message.content)
        else:
            raise Exception(f"Groq API returned no choices: {response}")

    async def ainvoke(self, input: str) -> LLMResponse:
        """Asynchronously invoke Groq's API."""
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": input
                }
            ],
            model=self.model_name
        )
        
        if response.choices:
            # Extract content from the response
            return LLMResponse(content=response.choices[0].message.content)
        else:
            raise Exception(f"Groq API returned no choices: {response}")
   


# llm = GroqLLM(groq_model_name)
llm = GroqLLM(model_name=groq_model_name, api_key=groq_api_key)



def generate_embedding(text):
    """Generates an embedding for the given text using Hugging Face model."""
    logger.info(f"Generating embedding for query: {text[:50]}...")
    embedding = embed_model.embed_documents([text])[0]
    logger.info(f"Generated embedding of length: {len(embedding)}")
    return embedding

def retrieve_similar_questions(query):
    """Retrieve semantically similar questions from Neo4j using the Neo4j GenAI package."""
    logger.info(f"Starting retrieval for query: {query}")

    embedding = llm.invoke(query).content

    # Initialize the retriever with custom LLM interface
    retriever = VectorRetriever(
        driver=driver,
        index_name=INDEX_NAME,
        embedder=embed_model,  # Use the custom HuggingFace LLM interface
        #top_k=2  # Retrieve top 5 similar results
    )

    # Perform the retrieval
    results = retriever.search(query_text=query, top_k=2)
    
    # If no results found
    if not results:
        logger.warning("No similar questions found.")
        return []
    
    # Collect the questions and their related nodes (Body, Topic, etc.)
    collected_results = []
    
    for label, items in results:  # Unpack the tuple ('items', [...])
        logger.info(f"Result Label: {label}")
        for result_item in items:  # Iterate through the list of items
            # Ensure result_item is a dictionary-like object before proceeding
            try:
                # Handle the '__retriever' case
                if isinstance(result_item, str) and result_item == "__retriever":
                    logger.info("Skipping '__retriever'")
                    continue
                
                # If it's a string, assume it's JSON-like content that needs parsing
                if isinstance(result_item, str):
                    # logger.info("Handling result_item as string")
                    content = eval(result_item)  # Convert string to a dictionary
                    question_id = content.get('id')

                # If it's a RetrieverResultItem, directly access its fields
                elif isinstance(result_item, RetrieverResultItem):
                    # logger.info("Handling result_item as RetrieverResultItem")
                    content = eval(result_item.content)  # Convert the content string into a dictionary
                    question_id = content.get('id')
                
                else:
                    logger.warning(f"Unhandled data type: {type(result_item)}")
                    continue
                
                logger.info(f"Found similar question: {content.get('text')} with ID: {question_id}")

                # Fetch related body and topic info
                with driver.session() as session:
                    body_result = session.run(
                        """
                        MATCH (q:Question {id: $qid})-[:HAS_BODY]->(b:Body)
                        RETURN b.text_link AS body_link
                        """, qid=question_id
                    ).single()

                    topic_result = session.run(
                        """
                        MATCH (q:Question {id: $qid})-[:HAS_TOPIC]->(t:Topic)
                        RETURN t.name AS topic
                        """, qid=question_id
                    ).single()

                collected_results.append({
                    "question": content.get("text"),
                    "body_link": body_result["body_link"] if body_result else None,
                    "topic": topic_result["topic"] if topic_result else None,
                })

            except Exception as e:
                logger.error(f"Error processing result_item: {e}")
    
    return collected_results
# def retrieve_similar_questions(query):
#     """Retrieve semantically similar questions from Neo4j using the Neo4j GenAI package."""
#     logger.info(f"Starting retrieval for query: {query}")

#     embedding = llm.invoke(query).content

#     # Initialize the retriever with custom LLM interface
#     retriever = VectorRetriever(
#         driver=driver,
#         index_name=INDEX_NAME,
#         embedder=embed_model,  # Use the custom HuggingFace LLM interface
#         #top_k=2  # Retrieve top 5 similar results
#     )

#     # Perform the retrieval
#     results = retriever.search(query_text=query, top_k=2)
    
#     # If no results found
#     if not results:
#         logger.warning("No similar questions found.")
#         return []
    
#     # Collect the questions and their related nodes (Body, Topic, etc.)
#     collected_results = []
#     for label, items in results:  # Unpack the tuple ('items', [...])
#         logger.info(f"Result Label: {label}")
#         for result_item in items:  # Iterate through the list of items
#             content = eval(result_item.content)  # Evaluate the string content as a dictionary
#             question_id = content.get('id')
#             logger.info(f"Found similar question: {content.get('text')} with ID: {question_id}")


#         with driver.session() as session:
#             body_result = session.run(
#                 """
#                 MATCH (q:Question {id: $qid})-[:HAS_BODY]->(b:Body)
#                 RETURN b.text_link AS body_link
#                 """, qid=question_id
#             ).single()

#             topic_result = session.run(
#                 """
#                 MATCH (q:Question {id: $qid})-[:HAS_TOPIC]->(t:Topic)
#                 RETURN t.name AS topic
#                 """, qid=question_id
#             ).single()

#         collected_results.append({
#             "question": content.get("text"),
#             "body_link": body_result["body_link"] if body_result else None,
#             "topic": topic_result["topic"] if topic_result else None,
#         })

#     return collected_results

def main():
    # Example query
    query = "What is the best diet for muscle gain?"

    # Perform retrieval
    results = retrieve_similar_questions(query)

    # Output the results
    for result in results:
        logger.info(f"Question: {result['question']}")
        logger.info(f"Related Body Link: {result['body_link']}")
        logger.info(f"Topic: {result['topic']}")

if __name__ == "__main__":
   

    # def log_available_groq_models():
    #     """Fetch and log available models from Groq API."""
    #     url = "https://api.groq.com/openai/v1/models"
    #     headers = {
    #         "Authorization": f"Bearer {groq_api_key}",
    #         "Content-Type": "application/json"
    #     }

    #     try:
    #         response = requests.get(url, headers=headers)
    #         response.raise_for_status()

    #         models = response.json().get('data', [])
    #         if models:
    #             logger.info("Available Groq models:")
    #             for model in models:
    #                 # Print the entire model data to understand its structure
    #                 logger.info(f"Model data: {model}")
    #                 # Attempt to log model id and description if they exist
    #                 model_id = model.get('id', 'Unknown ID')
    #                 model_description = model.get('description', 'No description available')
    #                 logger.info(f"Model: {model_id} - {model_description}")
    #         else:
    #             logger.warning("No models available or you do not have access to any models.")

    #     except requests.exceptions.HTTPError as http_err:
    #         logger.error(f"HTTP error occurred: {http_err}")
    #     except Exception as err:
    #         logger.error(f"An error occurred: {err}")

    # # Call the function to log available models
    # log_available_groq_models()


    main()



# ============================
# ============================
# ============================
# ============================
# ============================

# import os
# import logging
# from neo4j import GraphDatabase
# from neo4j_graphrag.retrievers import VectorRetriever
# from dotenv import load_dotenv
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from loguru import logger

# # TODO: Generate node with embedding for user question, link to the body associated with the top matching question, generate topic node for new question

# # Load environment variables
# load_dotenv()

# INDEX_NAME = "question-vector-index"

# # Neo4j Configuration
# neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
# neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
# neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

# # Connect to the Neo4j database
# driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
# logger.info("Neo4j driver initialized")

# # Hugging Face Embeddings Model (same model used for ingestion)
# embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# logger.info("Hugging Face Embeddings model loaded")

# def generate_embedding(text):
#     """Generates an embedding for the given text."""
#     logger.info(f"Generating embedding for query: {text[:50]}...")
#     embedding = embed_model.embed_documents([text])[0]
#     logger.info(f"Generated embedding of length: {len(embedding)}")
#     return embedding

# def retrieve_similar_questions(query):
#     """Retrieve semantically similar questions from Neo4j using the Neo4j GenAI package."""
#     logger.info(f"Starting retrieval for query: {query}")

#     # Initialize the retriever
#     retriever = VectorRetriever(
#         driver=driver,
#         index_name=INDEX_NAME,
#         embedding_fn=embed_model,  # Function to generate embeddings
#         # embedding_fn=embed_model.embed_query,  # Function to generate embeddings
#         top_k=2  # Retrieve top 5 similar results
#     )

#     # Perform the retrieval
#     results = retriever.retrieve(query)
    
#     # If no results found
#     if not results:
#         logger.warning("No similar questions found.")
#         return []
    
#     # Collect the questions and their related nodes (Body, Topic, etc.)
#     collected_results = []
#     for result in results:
#         question_id = result['id']
#         logger.info(f"Found similar question: {result['text']} with ID: {question_id}")

#         # Query for related nodes (Body, Topic, etc.)
#         with driver.session() as session:
#             # Get the body link associated with the question
#             body_result = session.run(
#                 """
#                 MATCH (q:Question {id: $qid})-[:HAS_BODY]->(b:Body)
#                 RETURN b.text_link AS body_link
#                 """, qid=question_id
#             ).single()

#             # Get the topic associated with the question
#             topic_result = session.run(
#                 """
#                 MATCH (q:Question {id: $qid})-[:HAS_TOPIC]->(t:Topic)
#                 RETURN t.name AS topic
#                 """, qid=question_id
#             ).single()

#         collected_results.append({
#             "question": result["text"],
#             "body_link": body_result["body_link"] if body_result else None,
#             "topic": topic_result["topic"] if topic_result else None,
#         })

#     return collected_results

# def main():
#     # Example query
#     query = "What is the best diet for muscle gain?"

#     # Perform retrieval
#     results = retrieve_similar_questions(query)

#     # Output the results
#     for result in results:
#         logger.info(f"Question: {result['question']}")
#         logger.info(f"Related Body Link: {result['body_link']}")
#         logger.info(f"Topic: {result['topic']}")

# if __name__ == "__main__":
#     main()




# =================================
# =================================
# =================================
# =================================
# =================================
# =================================
# =================================

# import os
# import logging
# from neo4j import GraphDatabase
# from neo4j_genai.retrievers import VectorRetriever
# from dotenv import load_dotenv
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from loguru import logger

# # TODO: Generate node with embedding for user question, link to the body associated with the top matching question, generate topic node for new question

# # Load environment variables
# load_dotenv()

# # Neo4j Configuration
# neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
# neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
# neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

# # Connect to the Neo4j database
# driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
# logger.info("Neo4j driver initialized")

# # Hugging Face Embeddings Model (same model used for ingestion)
# embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# logger.info("Hugging Face Embeddings model loaded")


# def generate_embedding(text):
#     """Generates an embedding for the given text."""
#     logger.info(f"Generating embedding for query: {text[:50]}...")
#     embedding = embed_model.embed_documents([text])[0]
#     logger.info(f"Generated embedding of length: {len(embedding)}")
#     return embedding

# def retrieve_similar_questions(query):
#     """Retrieve semantically similar questions from Neo4j using the Neo4j GenAI package."""
#     logger.info(f"Starting retrieval for query: {query}")

#     # When indexing is built in, build retriever like this
#     # retriever = VectorRetriever(driver, INDEX_NAME, embed_model)

#     retriever = VectorRetriever(
#         driver=driver,
#         embedding_fn=embed_model.embed_query,  # The function that returns an embedding for the query
#         top_k=2  # Number of top similar results to return
#     )

#     # Generate embedding for the input query
#     query_embedding = generate_embedding(query)
    
#     # Use Neo4j GenAI to search for similar questions
#     similar_questions = genai.find_similar("Question", "embedding", query_embedding)
    
#     # Collect the IDs and any associated information (e.g., body, topic)
#     results = []
#     for question in similar_questions:
#         logger.info(f"Found similar question: {question['text']}")
        
#         # Query for related nodes (Body, Topic, etc.)
#         with driver.session() as session:
#             body_result = session.run(
#                 """
#                 MATCH (q:Question {id: $qid})-[:HAS_BODY]->(b:Body)
#                 RETURN b.text_link AS body_link
#                 """, qid=question['id']
#             ).single()
            
#             topic_result = session.run(
#                 """
#                 MATCH (q:Question {id: $qid})-[:HAS_TOPIC]->(t:Topic)
#                 RETURN t.name AS topic
#                 """, qid=question['id']
#             ).single()

#         results.append({
#             "question": question["text"],
#             "body_link": body_result["body_link"] if body_result else None,
#             "topic": topic_result["topic"] if topic_result else None,
#         })

#     return results

# def main():
#     # Example query
#     query = "What is the best diet for muscle gain?"
    
#     # Perform retrieval
#     results = retrieve_similar_questions(query)
    
#     # Output the results
#     for result in results:
#         logger.info(f"Question: {result['question']}")
#         logger.info(f"Related Body Link: {result['body_link']}")
#         logger.info(f"Topic: {result['topic']}")

# if __name__ == "__main__":
#     main()
