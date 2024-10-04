from openai import OpenAI
import json
import os
import sys
from loguru import logger
import argparse
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

def call_openai_for_qa_pair(title, full_transcript):
    logger.debug(f"Calling OpenAI API for transcript: {title[:50]}...")
    logger.info(f"Transcript: {full_transcript}")

    prompt = f"""
        The following transcript is from a video of only 1 speaker, who is a doctor. It contains questions from others being read by speaker, followed by his answer. Your task is to return the first complete question and answer pair from the transcript, just as presented in the transcript. Follow these guidelines to ensure the response is valid, complete, and correctly formatted:

        1. **Text Output Only**: Return the result as pure text, with no extra text, explanations, or formatting outside of the content. The text content should follow these rules:
            - include the entire questions and answer as it appears in the transcript, without any modifications
           
        2. **No Code Blocks**: Do not enclose the text in markdown-style code blocks. Just return raw text.

        3. **No Modifications**: Do not alter, punctuate, summarize, or correct the text. The text should be returned exactly as it appears in the transcript, even if it contains grammatical errors, lacks punctuation, or appears disorganized.

        Return only the text with no additional explanation or formatting.
        Here are some examples of how he might transition from one question/answer to the next:
        - "keep up the good work you're doing great and we're sort of coming down on the last sort of few uh questions um but uh yeah this is one's from Andy Hall thank you very much Andy for the very generous Super Chat it's very kind of you um in your experience how long does it take for Crohn's to go into complete remission on Carnivore I'm 52-year-old male carnivore for three months doctor started me on uh what is.. "
        - "fixed and help your sleep acne or snoring as well and good luck with that Rick Diaz thank you very much for the Super Chat carnivore for six months down 35 pounds I'm 47 uh still high blood pressure 160 over 110 my doc wants to"

        These examples don't represent the total number of ways he might transition from an answer to the next question, but it's a good indication. He often tends to thank people for super chat or super sticker before reading their questions

        ## Transcript Data:
        transcript: {full_transcript}

    """
    # prompt = f"""
    #     The following transcript contains questions being read by a speaker, followed by the speaker's answer. Your task is to return the first complete question and answer pair from the transcript, formatted in a precise JSON structure. Follow these guidelines to ensure the response is valid and correctly formatted:

    #     1. **JSON Output Only**: Return the result as pure JSON, with no extra text, explanations, or formatting outside of the JSON structure. The JSON object should follow this exact format:
        
       
    #         "title": "The title of the entire transcript",
    #         "body": "The entire question and answer text as it appears in the transcript, without any modifications."
           

    #     2. **No Code Blocks**: Do not enclose the JSON in markdown-style code blocks. Just return raw JSON.

    #     3. **No Modifications**: Do not alter, punctuate, summarize, or correct the text in the "body" field. The text should be returned exactly as it appears in the transcript, even if it contains grammatical errors, lacks punctuation, or appears disorganized.

    #     4. **Quotation Marks in the Transcript**: If the text in the transcript contains quotation marks, ensure they are properly escaped to maintain valid JSON formatting. For example:
    #     - Incorrect: "He said, "hello."" (this would break the JSON format)
    #     - Correct: "He said, \"hello.\""

    #     5. **Consistent Formatting**: The response must be well-formed, valid JSON. Ensure that:
    #     - Keys are enclosed in double quotes.
    #     - Values are properly enclosed in double quotes if they are strings.
    #     - The JSON structure is valid, an object within a list, and can be parsed without errors.

    #     Return only the JSON object with no additional explanation or formatting.

    #     ## Transcript Data:
    #     title: {title}
    #     transcript: {full_transcript}

    # """
    # prompt = f"""
    # The transcript below has questions being read by a speaker, followed by the speaker's answer. 
    # Only return the first question/answer pair from the transcript, and do not alter, punctuate, summarize, or correct the text. 
    # Maintain the exact format and text as provided in the "body" field of the JSON output.
    # Do not enclose the json in a code block. Just provide the json.
    # DO NOT ALTER THE ORIGINAL TEXT IN ANY WAY. DO NOT CORRECT TYPOS, ADD PUNCTUATION, OR ADD CLARIFYING CONTEXT. PRESERVE THE ORIGINAL TEXT COMPLETELY.
    # AGAIN, NO PUNCTUATION
    # AGAIN, PLEASE RETURN VALID JSON
    
    # Transcript:
    # {full_transcript}
    
    # Return the output in this JSON format:
    # [
    # {{
    # "title": "{title}",
    # "body": "entire question and answer pair text here"
    # }}
    # ]
    # """

    # Call OpenAI API with the prompt
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Assuming you are using GPT-4 mini
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

    data= {
        "title": title,
        "body": output
    }
    return data

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
            data = call_openai_for_qa_pair(title, remaining_transcript)
        except Exception as e:
            logger.error(f"Stopping processing due to error: {e}")
            break
        
        # Write the new Q&A pair to the file immediately
        append_to_file(data)

        # Find the position of the processed chunk in the remaining transcript
        processed_chunk = data[0]['body']
        processed_chunk.replace("/", "")
        chunk_position = remaining_transcript.find(processed_chunk[-10:])

        if chunk_position == -1:
            logger.error("Could not find the processed chunk in the remaining transcript. Stopping.")
            break

        # Update the remaining transcript by slicing off the processed part
        remaining_transcript = remaining_transcript[chunk_position + len(processed_chunk):].strip()

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


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Process YouTube transcripts and extract Q&A pairs using OpenAI.")
    parser.add_argument("--json_file_path", "-f", type=str, help="The relative path to the JSON file containing the transcript.")
    
    args = parser.parse_args()

    json_file_path = args.json_file_path
    main(json_file_path)
