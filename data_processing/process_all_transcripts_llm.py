import os
import json
import ollama  
import re

def load_json(file_path):
    """Loads the JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data, file_path):
    """Saves the processed JSON data back to a file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# def extract_question_and_tags(text, model_name="llama2:latest"):
#     """
#     Uses Ollama's local model to extract the question from a given text
#     and generate a list of tags/keywords.
#     """
#     # Define the prompt for the model
#     prompt = f"""
#     You are given a section of a transcript. Your task is:
#     1. Extract the main question from the text.
#     2. Generate a list of tags or keywords that can help someone search for this information.

#     Section: {text}

#     Please respond with the question followed by a list of keywords.
#     """

#     # Run the prompt through the model using Ollama's API (assuming you have Ollama setup)
#     response = ollama.chat(model=model_name, messages=[
#     {
#         'role': 'user',
#         'content': prompt
#     }
# ])

#     # Parse the response, assuming the model provides a structured output
#     question, *tags = response.strip().split("\n")

#     # Clean the tags into a list of keywords
#     tags = [tag.strip() for tag in tags if tag]

#     return question, tags

def extract_question_and_tags(text, model_name="llama2:latest"):
    """
    Uses Ollama's local model to extract the question from a given text
    and generate a list of tags/keywords.
    """
    # Define the prompt for the model
    prompt = f"""
    You are given a transcript of a conversation. The transcript contains both the question
    and the response, but the question, while usually located toward the beginning of the body of text, is not explicitly marked. It may be fragmented or unclear
    and must be inferred from the response. Your tasks fall into two categories:

    Questions:
    1. Infer the most relevant question being answered in the transcript. Use the context of the response to help determine the question. 
    2. Only return the question portion of your response. DO NOT ADD ANY ADDITIONAL TEXT BEFORE OR AFTER THE QUESTION. 
    3. DO NOT PREPEND WITH 'QUESTION: ' OR 'INFERRED QUESTION: ' OR ANY OTHER TEXT. ONLY PROVIDE THE QUESTION.

    Keywords:
    1. Only return the list of keywords as strings.
    2. Do not include any numbers, symbols, or extra words like "Sure!", "Here are", "Keywords:", or other similar phrases.
    3. Each keyword should be a single word or short phrase without additional formatting.
    4. Return the list as plain strings, one keyword per line.
    5. DO NOT INCLUDE ANY NUMERATION, ADDITIONAL COMMENTS, OR ANY OTHER TEXT AT ALL. ONLY 1 KEYWORD PER INDEX AND NOTHING MORE
    6. DO NOT PREPEND WITH 'KEYWORDS: ' OR ANY OTHER TEXT. ONLY PROVIDE THE LIST OF KEYWORDS.

    The inferred question should be a complete sentence, as if someone had asked it directly.
    The tags should be one-word or simple keyword phrases, uniquely representative of the body of text. The tags should each point to a main topic of that section

    Transcript: {text}

    Please respond with the inferred question first, followed by a list of keywords.
    """

    # prompt = f"""
    # You are given a transcript of a conversation. The transcript contains both the question
    # and the response, but the question, while usually located toward the beginning of the body of text, is not explicitly marked. It may be fragmented or unclear
    # and must be inferred from the response. Your tasks fall into three categories:

    # Questions:
    # 1. Questions, if they explicitly exist in the text, can be in the form of a statement or phrased more as a question.
    # 2. Questions, if they explicitly exist in the text, are usually towards the beginning of the text body, after any 'thank you' or general chatting
    # 3. Regardless whether or not a question is found, to ensure usefulness, infer the most relevant question being answered in the transcript. Use the context of the response to help determine the question. 
    # 4. If a question was found, combine the question with inferred most relevant question to form a comprehensive question to represent the response
    # 5. If a question was not found, form a question based on inferred most relevant question from the text.
    # 6. Only return the question portion of your response. DO NOT ADD ANY ADDITIONAL TEXT BEFORE OR AFTER THE QUESTION. 

    # Keywords:
    # 1. Only return the list of keywords as strings, one keyword per string per index.
    # 2. Do not include any numbers, symbols, or extra words like "Sure!", "Here are", "Keywords:", or other similar phrases.
    # 3. Each keyword should be a single word or short phrase without additional formatting.
    # 4. Return the list as plain strings, one keyword per list index.
    # 5. DO NOT INCLUDE ANY NUMERATION, ADDITIONAL COMMENTS, OR ANY OTHER TEXT AT ALL. ONLY 1 KEYWORD PER INDEX AND NOTHING MORE

    # Date:
    # 1. Infer the date from the title. 
    # 2. Return date in the following format: 'yyyy-mm-dd'
    # 3. DO NOT INCLUDE ANY ADDITIONAL TEXT OR COMMENTS, PUNCTUATION OR SPACES. ONLY RESPOND WITH THE FORMATTED DATE

    # The inferred question should be a complete sentence, as if someone had asked it directly.
    # The tags should be one-word or simple keyword phrases, uniquely representative of the body of text. The tags should each point to a main topic of that section

    # Transcript: {text}

    # Please respond with the date first, followed by inferred question second, followed by a clean list of keywords last.

    # example response: '2023-01-01', 'Why arent I losing weight on the carnivore diet?', ['weight loss', 'calories', 'meat', 'exercise']
    # """
   
    

    # Run the prompt through the model using Ollama's API
    response = ollama.chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt
        }
    ])

    # Extract the message content from the response dictionary
    message_content = response['message']['content']

    # Split the response content into the inferred question and tags
    inferred_question, *tags = message_content.strip().split("\n")

    # Clean the tags into a list of keywords (using the previous cleaning function)
    clean_tags = clean_keywords(tags)

    return inferred_question, clean_tags


def extract_date_from_title(title, model_name="llama2:latest"):
    """
    Uses Ollama's local model to extract the date from given title
    """
    # Define the prompt for the model
    prompt = f"""
    You are given the title of a youtube informational video. Your tasks is to extract the date from the title if it exists and format as instructed below:

    1. Infer the date from the title. 
    2. Return date in the following format: 'yyyy-mm-dd'
    3. If a date does not exist, return None
    4. DO NOT APPEND OR PREPEND ANY TEXT OR SPACES TO THE FORMATTED DATE.
    5. DO NOT INCLUDE ANY ADDITIONAL TEXT OR COMMENTS, PUNCTUATION OR SPACES. ONLY RESPOND WITH THE FORMATTED DATE
    6. ONLY RETURN THE FORMATTED DATE STRING OR NONE

    Title: {title}
    """

    # Run the prompt through the model using Ollama's API
    response = ollama.chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt
        }
    ])

    # Extract the message content from the response dictionary
    message_content = response['message']['content']

    date = message_content.strip().split("\n")
    date = clean_date(date)

    return date

def extract_topic_from_question(question, model_name="llama2:latest"):
    """
    Uses Ollama's local model to extract the topic from a given question
    """
    # Define the prompt for the model
    prompt = f"""
    You are given the question. Your tasks is to extract the topic from the question if it exists and format as instructed below:

    1. Infer the topic from the question with the context of this question being asked on a youtube show about the benefits of the carnivore diet for humans.
    2. The topic should be between 1 and 3 words long.
    3. Given that the context is the carnivore diet, the topic should never be CARNIVORE DIET, as that is redundant.
    4. If a question does not exist, return None.
    5. DO NOT APPEND OR PREPEND ANY TEXT OR SPACES TO THE TOPIC.
    6. DO NOT INCLUDE ANY ADDITIONAL TEXT OR COMMENTS, PUNCTUATION OR SPACES. ONLY RESPOND WITH THE TOPIC.
    7. ONLY RETURN THE TOPIC STRING OR NONE.
    8. NEVER PREPEND TEXT LIKE 'TOPIC: '. ONLY RESPOND WITH THE ACTUAL TOPIC AND NOTHING MORE.

    Question: {question}
    """

    # Run the prompt through the model using Ollama's API
    response = ollama.chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt
        }
    ])

    # Extract the message content from the response dictionary
    message_content = response['message']['content']

    topic = message_content.strip().split("\n")[0]

    return topic


# def extract_date_from_title(title, model_name="llama2:latest"):
#     """
#     Uses Ollama's local model to extract the date from given title
#     """
#     # Define the prompt for the model
#     prompt = f"""
#     You are given the title of a youtube informational video. Your tasks is to extract the date from the title if it exists and format as instructed below:

#     1. Infer the date from the title. 
#     2. Return date in the following format: 'yyyy-mm-dd'
#     3. If a date does not exist, return None
#     4. DO NOT APPEND OR PREPEND ANY TEXT OR SPACES TO THE FORMATTED DATE.
#     5. DO NOT INCLUDE ANY ADDITIONAL TEXT OR COMMENTS, PUNCTUATION OR SPACES. ONLY RESPOND WITH THE FORMATTED DATE
#     6. ONLY RETURN THE FORMATTED DATE STRING OR NONE

#     Title: {title}
#     """

#     # Run the prompt through the model using Ollama's API
#     response = ollama.chat(model=model_name, messages=[
#         {
#             'role': 'user',
#             'content': prompt
#         }
#     ])

#     # Extract the message content from the response dictionary
#     message_content = response['message']['content']

#     date = message_content.strip().split("\n")
#     date = clean_date(date)

#     return date

def clean_keywords(raw_keywords):
    """
    Cleans the raw keywords by removing numbers, 'Keywords:' and other irrelevant data,
    returning a list of clean keyword strings.
    """
    clean_list = []
    for keyword in raw_keywords:
        # Remove any numerical indicators or unnecessary parts
        keyword = keyword.strip()
        keyword = keyword.lstrip("0123456789.- ")  # Remove numbers, dots, dashes, and spaces at the start
        keyword = keyword.replace("Keywords:", "")  # Remove 'Keywords:' text if present
        keyword = keyword.strip()  # Strip extra spaces again
        if keyword:  # Only append non-empty strings
            clean_list.append(keyword)
    return clean_list

def clean_date(raw_date):
    """Account for irregular llm output when inferring date"""
    # Regular expression to match dates in yyyy-mm-dd format
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    
    # Iterate through the data and extract the date
    
    for item in raw_date:
        match = date_pattern.search(item)
        if match:
            return match.group(0) 
    # for entry in raw_date:
    #     date_list = entry.get("date", [])
    #     for item in date_list:
    #         match = date_pattern.search(item)
    #         if match:
    #             return match.group(0) 


def process_batch_files(input_dir, model_name="llama2:latest"):
    """Processes all JSON files in the batch_processed_files directory."""
    for file_name in os.listdir(input_dir):
        if file_name.endswith("_processed.json"):
            file_path = os.path.join(input_dir, file_name)
            print(f"Processing file: {file_path}")

            # Load the JSON file
            data = load_json(file_path)

            # Process each section in the JSON data
            for section in data:
                text_body = section["transcript"]
                title = section["title"]

                # Use the LLM to extract the question and tags
                question, tags = extract_question_and_tags(text_body, model_name=model_name)
                date = extract_date_from_title(title, model_name=model_name)
                topic = extract_topic_from_question(question, model_name=model_name)

                # Add the extracted question and tags as metadata
                section.update({})
                section.update({
                    "question": question,
                    "topic": topic,
                    "date": date,
                    "body": {
                        "text": text_body,
                        "date": date,
                        "tags": tags
                    }
                })
                

            # Save the updated JSON file
            save_json(data, file_path)
            print(f"Processed file saved: {file_path}")

# Example usage:
input_directory = "data_processing/batched_processed_files"

# Process all files in the batch_processed_files directory
process_batch_files(input_directory, model_name="llama2:latest")
