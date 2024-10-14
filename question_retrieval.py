import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import LLMInterface, LLMResponse
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger
from groq import Groq
from neo4j_graphrag.types import RetrieverResultItem

# Load environment variables
load_dotenv()

INDEX_NAME = "carnivore1"
with open("tags_list.json", "r") as file:
    TAGS = json.load(file)

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
        self.client = Groq(api_key=self.api_key)

    def invoke(self, input: str) -> LLMResponse:
        """Invoke Groq's API synchronously."""
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": input}],
            model=self.model_name
        )
        if response.choices:
            return LLMResponse(content=response.choices[0].message.content)
        else:
            raise Exception(f"Groq API returned no choices: {response}")

    async def ainvoke(self, input: str) -> LLMResponse:
        """Asynchronously invoke Groq's API."""
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": input}],
            model=self.model_name
        )
        if response.choices:
            return LLMResponse(content=response.choices[0].message.content)
        else:
            raise Exception(f"Groq API returned no choices: {response}")

# Instantiate the Groq LLM
llm = GroqLLM(model_name=groq_model_name, api_key=groq_api_key)

def generate_embedding(text):
    """Generates an embedding for the given text using Hugging Face model."""
    logger.info(f"Generating embedding for query: {text[:50]}...")
    embedding = embed_model.embed_documents([text])[0]
    logger.info(f"Generated embedding of length: {len(embedding)}")
    return embedding

def retrieve_by_tags(query_tags, top_k=2):
    """
    Retrieve text bodies that match the most number of relevant tags from Neo4j.
    Returns top_k bodies with the highest number of matching tags.
    If multiple bodies have the same number of matches, all tied bodies are returned.
    """
    logger.info(f"Starting tag-based retrieval for tags: {query_tags}")

    # Dictionary to store body_ids and the number of matching tags
    body_match_count = {}

    with driver.session() as session:
        for tag in query_tags:
            # Fetch text bodies that are associated with the current tag
            results = session.run(
                """
                MATCH (b:Body)-[:HAS_TAG]->(t:Tag {word: $tag})
                RETURN b.id AS body_id, b.text_link AS body_link
                """, tag=tag
            ).values("body_id", "body_link")

            # Update the match count for each body_id
            for body_id, body_link in results:
                if body_id not in body_match_count:
                    body_match_count[body_id] = {
                        "body_link": body_link,
                        "matched_tags": set(),  # Keep track of matched tags
                        "match_count": 0
                    }
                body_match_count[body_id]["matched_tags"].add(tag)
                body_match_count[body_id]["match_count"] = len(body_match_count[body_id]["matched_tags"])

    # Sort bodies by the number of matching tags, in descending order
    sorted_bodies = sorted(body_match_count.values(), key=lambda x: x["match_count"], reverse=True)

    # Find the top k bodies with the highest number of matching tags
    top_results = []
    top_match_count = sorted_bodies[0]["match_count"] if sorted_bodies else 0

    for body in sorted_bodies:
        if body["match_count"] < top_match_count and len(top_results) >= top_k:
            break
        top_results.append({
            "body_link": body["body_link"],
            "matched_tags": list(body["matched_tags"]),
            "match_count": body["match_count"]
        })

    logger.info(f"Retrieved {len(top_results)} results by tags")
    return top_results

def question_retrieval(query):
    """Retrieve semantically similar questions from Neo4j using vector similarity (cosine)."""
    logger.info(f"Starting retrieval for query: {query}")

    # Generate query embedding using Hugging Face
    embedding = generate_embedding(query)

    # Initialize the VectorRetriever (Neo4j will use cosine similarity if set in the index)
    retriever = VectorRetriever(
        driver=driver,
        index_name=INDEX_NAME,
        embedder=embed_model,
    )

    # Perform the vector search
    results = retriever.search(query_text=query, top_k=2)

    if not results:
        logger.warning("No similar questions found.")
        return []

    # Collect the questions and their related nodes (Body, Tags, etc.)
    collected_results = []

    for label, items in results:  # 'label' is 'items', 'items' is the list of RetrieverResultItem
        logger.debug(f"RESULT LABEL: {label}")
        for result_item in items:  # Iterate over the RetrieverResultItem objects
            if isinstance(result_item, str):
                logger.debug(f"Skipping result_item: {result_item}")
                continue

            logger.debug(f"RESULT ITEM: {result_item}")
            try:
                content = eval(result_item.content)  # Convert content to dictionary
                question_id = content['id']
                question_text = content['text']
                logger.info(f"Found similar question: {question_text} with ID: {question_id}")

                # Fetch related Body and Tags info from Neo4j
                with driver.session() as session:
                    body_result = session.run(
                        """
                        MATCH (q:Question {id: $qid})-[:HAS_BODY]->(b:Body)
                        RETURN b.id AS body_id, b.text_link AS body_link
                        """, qid=question_id
                    ).single()
                    logger.info(f"BODY RESULT: {body_result}")

                    # Fetch all tags for the body
                    tags_result = session.run(
                        """
                        MATCH (b:Body {id: $bid})-[:HAS_TAG]->(t:Tag)
                        RETURN t.word AS tags
                        """, bid=body_result["body_id"]
                    ).values("tags")  # Use .values() to return all tag values as a list

                    # Flatten the tags_result into a 1D array
                    flat_tags_result = [tag for sublist in tags_result for tag in sublist]
                    logger.info(f"FLATTENED TAGS RESULT: {flat_tags_result}")

                collected_results.append({
                    "question": question_text,
                    "body_link": body_result["body_link"] if body_result else None,
                    "tags": flat_tags_result if flat_tags_result else None,  
                    # Flatten the tags_result into a 1D array
                    

                })

            except Exception as e:
                logger.error(f"Error processing result_item: {e}")

    return collected_results




def main():
    # Example query
    query = "What is the best diet for muscle gain?"

    # Perform retrieval
    results = question_retrieval(query)

    # Output the results
    for result in results:
        logger.info(f"Question: {result['question']}")
        logger.info(f"Related Body Link: {result['body_link']}")
        logger.info(f"Tags: {result['tags']}")  # Updated this line to log 'tags'


if __name__ == "__main__":
    # main()

    import sys
    logger.info(f"Retrieval Path: {sys.path}")
