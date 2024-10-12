import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

with open("tags_list.json", "r") as file:
    TAGS = json.load(file)

# Neo4j Configuration
neo4j_password = os.getenv("NEO4JAURA_INSTANCE_PASSWORD")
neo4j_username = os.getenv("NEO4JAURA_INSTANCE_USERNAME")
neo4j_uri = os.getenv("NEO4JAURA_INSTANCE_URI")

# Connect to the Neo4j database
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
logger.info("Neo4j driver initialized")


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


def test_tag_retrieval():
    """Test tag retrieval with a sample set of query tags."""
    query_tags = [
        "Beginner",
  "Dairy",
  "Lifestyle",
  "Metabolic Health",
  "Mental and Cognitive Health",
  "Exercise and Physical Performance",
  "Inflammation and Autoimmune Conditions",
  "Gut Health",
  "Nutritional Myths and Misconceptions",
    ]  # Example query tags to search for
    # query_tags = ["Salt", ]  # Example query tags to search for
    logger.info(f"Running tag-based retrieval for tags: {query_tags}")

    # results = retrieve_by_tags(TAGS, top_k=2)
    results = retrieve_by_tags(query_tags, top_k=2)

    # Display results
    if results:
        for idx, result in enumerate(results, start=1):
            logger.info(f"Result {idx}:")
            logger.info(f"Body Link: {result['body_link']}")
            logger.info(f"Matched Tags: {result['matched_tags']}")
            logger.info(f"Number of Matches: {result['match_count']}")
    else:
        logger.info("No results found for the given tags.")


if __name__ == "__main__":
    # Run the tag retrieval test
    test_tag_retrieval()
