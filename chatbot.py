import requests
import json
from openai import OpenAI
from groq import Groq
from question_retrieval import question_retrieval  
from tag_retrieval import tag_retrieval, retrieve_by_tags
from loguru import logger
import os

# Load environment variables for API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model_name = "llama3-8b-8192"

with open("tags_list.json", "r") as file:
    TAGS = json.load(file)

# Initialize OpenAI client (assuming it has been initialized correctly in your environment)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Groq LLM client initialization
groq_client = Groq(api_key=groq_api_key)
client = OpenAI(api_key=openai_api_key)

def fetch_body_text_from_links(body_links):
    """Fetches the text content from body links."""
    texts = []
    for link in body_links:
        response = requests.get(link)
        if response.status_code == 200:
            texts.append(response.text)
            # logger.info("response")
        else:
            logger.warning(f"Failed to fetch body link: {link}")
    return texts

def combine_context(user_input, body_texts):
    """Combines user input and body texts into a single context prompt."""
    combined_context = f"User question: {user_input}\n\nContext:\n"
    for i, body_text in enumerate(body_texts):
        combined_context += f"---\nContext {i+1}:\n{body_text}...\n" 
        # combined_context += " ---\nPlease read through the following information carefully and respond using the most relevant parts to answer the question. If the context doesn't provide a clear yes or no, explain any nuances or relevant insights based on the information available.\n"
    return combined_context

def query_openai(system_prompt, user_prompt):
    """Query OpenAI with the given system and user prompts."""

    logger.info(f"PROMPT: {user_prompt}" + " ---\nPlease read through the following information carefully and respond using the most relevant parts to answer the question. If the context doesn't provide a clear yes or no, explain any nuances or relevant insights based on the information available.\n")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        logger.debug("Successfully received response from OpenAI.")
        logger.info(f"response: {response}")
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {e}")
        raise e

    output = response.choices[0].message.content.strip()
    return output

def query_groq(prompt):
    """Query Groq with the given prompt."""
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=groq_model_name
    )
    if response.choices:
        return response.choices[0].message.content.strip()
    else:
        raise Exception(f"Groq API returned no choices: {response}")
    
def get_user_input_tags(user_input):
    """generates tags for user query"""
    system_prompt = f"""
    You are a helpful assistant responsible for assigning appropriate tags to a given question or phrase.
    Your task is to carefully analyze the input provided by the user and assign one or more tags based on the topics discussed. 
    You must select from the following list of distinct tags:
    {TAGS}

    An appropriate tag is one that represents a topic mentioned or touched upon in some way in the user's input. 
    If a topic is not clearly mentioned or implied, do not assign the corresponding tag. 
    Return all applicable tags in a Python list format.

    If no appropriate tags can be found, return an empty list.
    """

    user_prompt = f"""
    Assign the appropriate tags to the following input: 
    "{user_input}"

    Remember to carefully select only the tags that represent topics touched on in the input from the list provided in the system prompt.
    """

    schema = {
        "name": "tag_response",  # Name of the schema
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {  # Define the properties of the object
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["tags"],  # Ensure that "tags" is required
            "additionalProperties": False
        }
    }
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1500,
            response_format={"type": "json_schema", "json_schema": schema}
        )
        logger.debug("Successfully received response from OpenAI.")
        logger.info(f"response: {response}")
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {e}")
        raise e

    output = response.choices[0].message.content.strip()
    return output



def generate_chat_response(user_input, use_groq=False):
    """Generates a response from either OpenAI or Groq, based on the user's choice."""
    # Step 1: Retrieve similar questions and their body links
    query_tags = get_user_input_tags(user_input)
    results_by_question = question_retrieval(user_input)
    results_by_tag = retrieve_by_tags(query_tags)
    # results_by_tag = tag_retrieval(query_tags)
    body_links = [result['body_link'] for result in (results_by_question + results_by_tag) if result['body_link']]
    
    if not body_links:
        return "Sorry, I couldn't find enough information to answer your question."

    # Step 2: Fetch the text from the body links
    body_texts = fetch_body_text_from_links(body_links)

    # Step 3: Combine user input and context
    combined_context = combine_context(user_input, body_texts)
    
    # system_prompt = (
    #     "You are an assistant designed to answer questions based solely on the provided context. "
    #     "Do not use any prior knowledge or training data. If the provided context is insufficient "
    #     "to answer the user's question, reply with 'I don't have enough information to answer this question.'"
    # )
    system_prompt = """
        You are an assistant designed to answer questions based solely on the provided context. Your goal is to provide as much relevant detail from the context as possible without introducing any information from your prior training or knowledge that is not found in the context. 
        If the context contains relevant information that addresses the user's question, even if the answer is complex or ambiguous, provide that information in full. 
        If there is no direct answer, offer the most relevant insights based on the context without making unsupported assumptions or conclusions. 
        If the provided context is not sufficient to address the user's question at all, reply with 'I don't have enough information to answer this question.'
        """

    
    # Step 4: Query the appropriate model (OpenAI or Groq)
    if use_groq:
        return query_groq(combined_context)
    else:
        return query_openai(system_prompt, combined_context)


if __name__ == "__main__":
    # Example usage with OpenAI:
    # user_input = "What is the best diet for muscle gain?"
    # response = generate_chat_response(user_input, use_groq=True)
    # logger.info(f"Response from OpenAI: {response}")

    # Example usage with Groq:
    # response_groq = generate_chat_response(user_input, use_groq=True)
    # logger.info(f"Response from Groq: {response_groq}")
    import sys
    logger.info(f"Chatbot Path: {sys.path}")

    get_user_input_tags("Is dairy in my diet giving me Alzheimer's?")