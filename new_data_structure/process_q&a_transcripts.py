from openai import OpenAI
import json
import os
import sys
from loguru import logger
import argparse
from dotenv import load_dotenv

load_dotenv()

# Set up your OpenAI API key
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Configure loguru logging
logger.add("transcript_processing.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB")

def call_openai_for_qa_pair(title, full_transcript):
    logger.debug(f"Calling OpenAI API for transcript: {title[:50]}...")
    logger.info(f"Transcript: {full_transcript}")

    # Define the prompt
    prompt = f"""
    The transcript below has questions being read by a speaker, followed by the speaker's answer. 
    Only return the first question/answer pair from the transcript, and do not alter, punctuate, summarize, or correct the text. 
    Maintain the exact format and text as provided in the "body" field of the JSON output.
    
    Transcript:
    {full_transcript}
    
    Return the output in this JSON format:
    [
    {{
    "title": "{title}",
    "body": "entire question and answer pair text here"
    }}
    ]
    """

    # Call OpenAI API with the prompt
    try:
        response = client.chat.completions.create(
            model="gpt-4-mini",  # Assuming you are using GPT-4 mini
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        logger.debug("Successfully received response from OpenAI.")
        logger.info(f"response: {response}")
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {e}")
        raise e

    # Extract the response
    output = response.choices[0].message.content.strip()
    return output

def append_to_file(data, filename="1_processed.json"):
    logger.debug(f"Appending processed chunk to file: {filename}")
    
    # Append the data to the JSON file
    if os.path.exists(filename):
        # Read the existing file
        with open(filename, 'r') as file:
            existing_data = json.load(file)
    else:
        existing_data = []

    # Append the new data to the existing data
    existing_data.append(data)

    # Write the updated data back to the file
    with open(filename, 'w') as file:
        json.dump(existing_data, file, indent=2)

    logger.debug(f"Successfully appended data to {filename}.")

def process_transcript(title, full_transcript):
    logger.info(f"Starting transcript processing for: {title}")
    remaining_transcript = full_transcript

    while remaining_transcript:
        try:
            # Call OpenAI for the next Q&A pair
            output = call_openai_for_qa_pair(title, remaining_transcript)
        except Exception as e:
            logger.error(f"Stopping processing due to error: {e}")
            break
        
        # Extract the processed Q&A pair
        try:
            processed_chunk = json.loads(output)[0]['body']
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Error in processing the response: {e}")
            break
        
        # Create a data object with title and body
        data = {"title": title, "body": processed_chunk}
        
        # Write the new Q&A pair to the file immediately
        append_to_file(data)

        # Remove the processed chunk from the transcript
        remaining_transcript = remaining_transcript.replace(processed_chunk, "", 1).strip()

    logger.info("Transcript processing complete.")

def main(json_file_path):
    

    logger.info(f"Loading transcript from file: {json_file_path}")

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            title = data['title']
            transcript = data['transcript']
            logger.info(f"Successfully loaded transcript: {title}")
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON in file: {json_file_path}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Missing expected key {e} in the provided JSON file.")
        sys.exit(1)

    process_transcript(title, transcript)

# If running the script from the command line
if __name__ == "__main__":
    # Argument parsing using argparse
    parser = argparse.ArgumentParser(description="Process YouTube transcripts and extract Q&A pairs using OpenAI.")
    parser.add_argument("json_file_path", type=str, help="The relative path to the JSON file containing the transcript.")
    
    args = parser.parse_args()

    json_file_path = args.json_file_path
    main(json_file_path)
