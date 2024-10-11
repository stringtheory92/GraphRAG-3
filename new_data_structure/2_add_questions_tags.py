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

TAGS = ["Beginner",
        "Dairy", 
        "Lifestyle",
        "Metabolic Health",
        "Mental and Cognitive Health",
        "Exercise and Physical Performance",
        "Inflammation and Autoimmune Conditions",
        "Gut Health",
        "Nutritional Myths and Misconceptions",
        "Fruit Sugar and Carbohydrates",
        "Disease Prevention",
        "Sustainability and Ethics",
        "Ketosis and Fat Adaptation",
        "Vitamin and Nutrient Deficiencies",
        "Fasting",
        "Autophagy",
        "Cholesterol and Heart Disease",
        "Weight Loss and Fat Loss",
        "Cancer",
        "Sleep and Recovery",
        "Skin Health",
        "Hormonal Balance",
        "Carnivore for Children and Families",
        "Evolutionary Nutrition",
        "Anti-Aging and Longevity",
        "Food Addiction",
        "Electrolytes and Hydration",
        "Reproductive Health",
        "Histamine Intolerance",
        "Food Sensitivities",
        "Thyroid Health",
        "Salt",
        "Muscle Building and Protein Intake",
        "Bone Health and Joint Pain",
        "Sleep Apnea",
        "Chronic Fatigue Syndrome",
        "Vitamin D","Sunlight",
        "Carb Cycling",
        "Fat Protein Ratio",
        "Dental Health",
        "Mood Stabilization and Anxiety",
        "Hyperinsulinemia",
        "Sarcopenia Prevention",
        "Osteoporosis",
        "Liver Health",
        "Digestive Health",
        "Constipation and Diarrhea",
        "Alzheimer's", 
        "Taking statins", 
        "Tumor", 
        "Other professors or doctors", 
        "carnivore athletes",
        "Malabsorption",
        "Glycogen",
        "Organ Meats",
        "Fiber",
        "Meat Aversion",
        "Tryptophan",
        "Blue Zones",
        "Veganism",
        "Arrhythmia",
        "Pregnancy",
        "Vegetarianism",
        "Studies in nutrition science",
        "Dietetics Association",
        "Seventh Day Adventist Church",
        "Butter",
        "Community",
        "Insomnia",
        "CDB",
        "Autism",
        "Depression",
        "Major Carnivore Recovery Stories",
        "Epilepsy",
        "Hydration",
        "Seed Oils",
        "Anthropology",
        "Medication",
        "Kids",
        "Elderly",
        "Oral health",
        "Blood clots",
        "Vascular issues",
        "Coffee",
        "Kidneys",
        "Cholesterol",
        "Inuit",
        "Maasai",
        "Kikuyu",
        "Ancel Keys",
        "Paul Saladino",
        "Statistics",
        "Narcolepsy",
        "Life expectancy",
        "Calcium",
        "Testosterone",
        "Estrogen",
        "Ovaries",
        "Big Rant (used for outsized text bodies)",
        "Potassium",
        "Magnesium",
        "Sleep",
        "Goat",
        "Lamb",
        "ADHD",
        "Grass-Fed",
        "Omega-3 and Omega-6",
        "B12",
        "Cyanide",
        "Fatty Liver",
        "Gluconeogenesis",
        "Acne",
        "Urea and Creatinine",
        "Protein Powders",
        "Polyps",
        "Dopamine",
        "Alcohol",
        "Cannabis",
        "Genetics",
        "Cecum",
        "Primates",
        "CAC Score",
        "Melatonin",
        "Probiotics",
        "Gallstones",
        "Anorexia",
        "mRNA",
        "GMO",
        "Artificial Sweeteners",
        "Fertility and Sterility",
        "Agricultural Revolution",
        "Ice Age",
        "Migraine",
        "Body Odor",
        "Moisturizers",
        "Essential Oils",
        "Psoriasis",
        "Arthritis",
        "Randle Cycle",
        "Framingham Heart Study",
        "American Heart Association",
        "Proctor and Gamble",
        "Gout",
        "Oxalates",
        "Oxalate Stones",
        "Kidney Stones",
        "Parkinson’s",
        "Rapid Heartbeat",
        "Histamines",
        "Gallstones",
        "Hair loss",
        "A1C or hbA1C",
        "Fat to Protein Ratio",
        "High A1C",
        "High Triglycerides",
        "Fasting Insulin",
        "Insulin",
        "Caffeine",
        "Morality of Eating Meat",
        "Farming vs Ranching on Wildlife and Environment",
        "Monocropping",
        "Antibiotics",
        "Eczema",
        "Schatzki’s Ring",
        "Diverticulitis and Diverticulosis",
        "Amyloid plaque",
        "Chelating agent - pull toxic chemicals out of your body",
        "Cheating on the carnivore diet (come up with a more concise term for this)"
        
        ]

def generate_question_tags(excerpt):
    logger.debug(f"Generating question and tags for excerpt:")
    logger.info(f"{excerpt}")

    user_prompt = f"""
        You are given an excerpt of a video transcript (YouTube live Ask Me Anything) in which a doctor is reading questions or comments from the carnivore diet community and then responding to the best of his ability. 
        The transcript contains both the community member's question or comment first (as read by the doctor), followed by his response.
        Due to the context of the AMA format with Super Chats, etc, the question or comment as presented may be fragmented or unclear.
        Your tasks fall into two categories: 
        1. Generate a complete and comprehensive question.
        2. Generate a list of tags as a subset of a provided list of available tags that represent the content in the excerpt.

    Questions:
    1. Infer the most relevant question being answered in the transcript. Use both the question at the beginning of the excerpt (if it exists) and the context of the entire response to help determine the complete question. 
    2. Only return the question portion of your response. DO NOT ADD ANY ADDITIONAL TEXT BEFORE OR AFTER THE QUESTION. 
    3. DO NOT PREPEND WITH 'QUESTION: ' OR 'INFERRED QUESTION: ' OR ANY OTHER TEXT. ONLY PROVIDE THE QUESTION.

    Tags:
    1. Only return the list of tags as strings.
    2. Do not include any numbers, symbols, or extra words like "Sure!", "Here are", "Keywords:", or other similar phrases.
    3. Each tag must be from the provided TAGS_LIST without additional formatting.
    4. Include all tags within TAGS_LIST that represent topics touched on within the excerpt.
    5. DO NOT INCLUDE ANY NUMERATION, ADDITIONAL COMMENTS, OR ANY OTHER TEXT AT ALL. ONLY 1 KEYWORD PER INDEX AND NOTHING MORE
    6. DO NOT PREPEND WITH 'KEYWORDS: ' OR ANY OTHER TEXT. ONLY PROVIDE THE LIST OF KEYWORDS.

    The inferred question should be a complete sentence, as if someone had asked it directly, ending in a ?
    The tags must exist in TAGS_LIST to be included in your response, and representative of some portion of the excerpt. 
    Consider each tag in TAGS_LIST and carefully select the ones that represent some portion of information in the excerpt

    Excerpt: {excerpt}
    TAGS_LIST: {TAGS}

    Please respond with the inferred question first, followed by a list (python list - []) of tags.

    """

    system_prompt = """
    You are an expert assistant tasked with processing excerpts of video transcripts. These transcripts come from a YouTube live "Ask Me Anything" session where a doctor reads questions or comments from the carnivore diet community and responds to them. Your responsibility is to:
    1. Accurately infer and generate a complete, coherent question based on the fragmented or unclear input at the beginning of the excerpt and the context provided by the doctor’s full response.
    2. Identify relevant topics from the provided tags list that are representative of the content in the excerpt.

    To achieve this:
    1. Focus on reconstructing the most relevant question. The question must be complete, coherent, and inferred from the entirety of the transcript excerpt.
    2. When producing the question, **only** output the inferred question as a standalone sentence. Do not include any additional text, explanation, labels, or preambles such as "Question:".
    3. In the second task, output **only** a list of tags relevant to the excerpt. Each tag must be directly selected from the provided TAGS_LIST. Do not add any additional words, symbols, numeration, or explanations in your response.
    4. Your responses must be formatted as follows:
    - First, provide the inferred question.
    - Immediately after, provide a list of tags (one per line) relevant to the excerpt, without any added text or comments.
    5. Ensure that both the inferred question and the tags are based solely on the transcript excerpt provided and strictly adhere to the instructions.
"""

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
    # return output
    try:
        # output = output.split("?")
        # logger.info(f"Stage 1: {output}")
        # question = output[0].strip() + "?"
        # logger.info(f"Stage 2: {output}")
        # logger.info(f"Stage 2: {question}")
        # tags = json.loads(output[1].strip())  # Convert the stringified list to an actual list

        # logger.debug(f"Generated question: {question}")
        # logger.debug(f"Generated tags: {tags}")

    
        output = output.split("?", 1)  # Split by the first occurrence of '?'
        logger.info(f"Stage 1: {output}")
        
        # Extract the question and ensure it ends with a question mark
        question = output[0].strip() + "?"
        logger.info(f"Stage 2 - Question: {question}")
        
        # Manually parse the tags list from the second part of the response
        tags_str = output[1].strip()
        
        # Remove any extraneous characters around the list (like newlines or spaces) and evaluate it as a list
        tags = eval(tags_str)
        
        logger.debug(f"Generated question: {question}")
        logger.debug(f"Generated tags: {tags}")

        return question, tags
    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {e}")
        raise e

# def process_data(json_data, output_dir="./2_1_added_qt", error_log_file="error_segments.json"):
#     sanitized_title = json_data[0]["title"].replace(" ", "_").replace("/", "_")  
#     output_dir = os.path.join(output_dir, f"PQT_{sanitized_title}.json")
    
#     # Ensure that the output directory exists
#     os.makedirs(output_dir, exist_ok=True)

#     if not os.path.exists(output_dir):
#         with open(output_dir, 'w') as f:
#             json.dump([], f)

#     logger.info(f"Starting transcript processing for: {json_data[0]['title']}")
#     for idx, segment in enumerate(json_data):
#         body = segment["body"]
#         title = segment["title"]
#         try:
#             question, tags = generate_question_tags(body)

#             logger.info(f"Successfully processed segment {idx}")
            
#             segment["question"] = question
#             segment["tags"] = tags  # This will now be a proper list
            
#             with open(output_dir, 'r') as f:
#                 existing_data = json.load(f)

#             existing_data.append(segment)

#             with open(output_dir, 'w') as f:
#                 json.dump(existing_data, f, indent=2)

#             logger.info(f"Segment appended to {output_dir}")

#         except Exception as e:
#             logger.error(f"Error processing segment {idx}: {e}")
#             write_failed_segment(idx, body, error_log_file)
#             continue  
#     # for idx, segment in enumerate(json_data):
#     #     body = segment["body"]
#     #     title = segment["title"]
#     #     try:
#     #         output = generate_question_tags(body)

#     #         try:
#     #             output = output.split("?")
#     #             output = [val.strip() for val in output]

#     #             question = output[0] + "?"
#     #             tags = [tag.strip() for tag in output[1].splitlines() if tag.strip()]

#     #             logger.info(f"Successfully processed segment {idx}")
                
#     #             segment["question"] = question
#     #             segment["tags"] = tags
                
#     #             with open(output_dir, 'r') as f:
#     #                 existing_data = json.load(f)

#     #             existing_data.append(segment)

#     #             with open(output_dir, 'w') as f:
#     #                 json.dump(existing_data, f, indent=2)

#     #             logger.info(f"Segment appended to {output_dir}")

#     #         except Exception as e:
#     #             logger.error(f"Error processing segment {idx}: {e}")
#     #             write_failed_segment(idx, body, error_log_file)
#     #             continue  

#     #     except Exception as e:
#     #         logger.error(f"Stopping processing of transcript due to error: {e}")
#     #         break

#     logger.info("Transcript processing complete.")

def process_data(json_data, output_dir="./2_1_added_qt", error_log_file="error_segments.json"):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create the output file path by using the title of the segment
    sanitized_title = json_data[0]["title"].replace(" ", "_").replace("/", "_")  
    output_file_path = os.path.join(output_dir, f"PQT_{sanitized_title}.json")
    
    # Initialize the output file if it doesn't exist
    if not os.path.exists(output_file_path):
        with open(output_file_path, 'w') as f:
            logger.info(f"Initializing {output_file_path}")
            json.dump([], f)

    logger.info(f"Starting transcript processing for: {json_data[0]['title']}")

    for idx, segment in enumerate(json_data):
        body = segment["body"]
        title = segment["title"]
        try:
            # Generate question and tags
            question, tags = generate_question_tags(body)

            try:
                # # Process the question and tags
                # output = output.split("?")
                # output = [val.strip() for val in output]

                # question = output[0] + "?"
                # tags = [tag.strip() for tag in output[1].splitlines() if tag.strip()]

                logger.info(f"Successfully processed segment {idx}")
                
                # Update the segment with the new data
                segment["question"] = question
                segment["tags"] = tags
                
                # Load existing data from the file
                with open(output_file_path, 'r') as f:
                    existing_data = json.load(f)

                # Append the new segment data to the existing data
                existing_data.append(segment)

                # Write the updated data back to the file
                with open(output_file_path, 'w') as f:
                    json.dump(existing_data, f, indent=2)

                logger.info(f"Segment appended to {output_file_path}")

            except Exception as e:
                logger.error(f"Error processing segment {idx}: {e}")
                write_failed_segment(idx, body, error_log_file)
                continue  

        except Exception as e:
            logger.error(f"Stopping processing of transcript due to error: {e}")
            break

    logger.info("Transcript processing complete.")

def write_failed_segment(segment_index, body, error_log_file):
    failed_segment = {"segment_index": segment_index, "body": body}

    if os.path.exists(error_log_file):
        with open(error_log_file, 'r+') as file:
            error_data = json.load(file)
            error_data.append(failed_segment)
            file.seek(0)
            json.dump(error_data, file, indent=2)
    else:
        with open(error_log_file, 'w') as file:
            json.dump([failed_segment], file, indent=2)

    logger.info(f"Segment {segment_index} written to {error_log_file} for later review.")

def process_directory(directory_path):
    """Process all JSON files in the specified directory."""
    for file_name in os.listdir(directory_path):
        if file_name.endswith(".json"):
            json_file_path = os.path.join(directory_path, file_name)
            logger.info(f"Processing file: {json_file_path}")
            main(json_file_path)

def main(json_file_path):
    logger.info(f"Loading data from file: {json_file_path}")

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded data from transcript: {data[0]['title']}")
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON in file: {json_file_path}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Missing expected key {e} in the provided JSON file.")
        sys.exit(1)

    process_data(data)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Process YouTube transcripts and extract Q&A pairs using OpenAI.")
    parser.add_argument("--json_file_path", "-f", type=str, help="The relative path to the JSON file containing the transcript.")
    parser.add_argument("--dir", "-d", type=str, help="The relative path to a directory of JSON files.")

    args = parser.parse_args()

    if args.dir:
        process_directory(args.dir)
    elif args.json_file_path:
        main(args.json_file_path)
    else:
        logger.error("You must provide either a --json_file_path or a --dir argument.")
        sys.exit(1)



# from openai import OpenAI
# import json
# import os
# import sys
# from loguru import logger
# import argparse
# from dotenv import load_dotenv

# load_dotenv()

# client = OpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY")
# )

# TAGS = ["Beginner","Dairy", "Lifestyle","Metabolic Health","Mental and Cognitive Health","Exercise and Physical Performance","Inflammation and Autoimmune Conditions","Gut Health","Nutritional Myths and Misconceptions","Fruit Sugar and Carbohydrates","Disease Prevention","Sustainability and Ethics","Ketosis and Fat Adaptation","Vitamin and Nutrient Deficiencies","Fasting","Autophagy","Cholesterol and Heart Disease","Weight Loss and Fat Loss","Cancer","Sleep and Recovery","Skin Health","Hormonal Balance","Carnivore for Children and Families","Evolutionary Nutrition","Anti-Aging and Longevity","Food Addiction","Electrolytes and Hydration","Reproductive Health","Histamine Intolerance","Food Sensitivities","Thyroid Health","Salt","Muscle Building and Protein Intake","Bone Health and Joint Pain","Sleep Apnea","Chronic Fatigue Syndrome","Vitamin D","Sunlight","Carb Cycling","Fat Protein Ratio","Dental Health","Mood Stabilization and Anxiety","Hyperinsulinemia","Sarcopenia Prevention","Osteoporosis","Liver Health","Digestive Health","Constipation and Diarrhea", "Alzheimer's", "Taking statins", "Tumor", "Other professors or doctors", "carnivore athletes"]

# def generate_question_tags(excerpt):
#     logger.debug(f"Generating question and tags for excerpt:")
#     logger.info(f"{excerpt}")

#     user_prompt = f"""
#         You are given an excerpt of a video transcript (YouTube live Ask Me Anything) in which a doctor is reading questions or comments from the carnivore diet community and then responding to the best of his ability. 
#         The transcript contains both the community member's question or comment first (as read by the doctor), followed by his response.
#         Due to the context of the AMA format with Super Chats, etc, the question or comment as presented may be fragmented or unclear.
#         Your tasks fall into two categories: 
#         1. Generate a complete and comprehensive question.
#         2. Generate a list of tags as a subset of a provided list of available tags that represent the content in the excerpt.

#     Questions:
#     1. Infer the most relevant question being answered in the transcript. Use both the question at the beginning of the excerpt (if it exists) and the context of the entire response to help determine the complete question. 
#     2. Only return the question portion of your response. DO NOT ADD ANY ADDITIONAL TEXT BEFORE OR AFTER THE QUESTION. 
#     3. DO NOT PREPEND WITH 'QUESTION: ' OR 'INFERRED QUESTION: ' OR ANY OTHER TEXT. ONLY PROVIDE THE QUESTION.

#     Tags:
#     1. Only return the list of tags as strings.
#     2. Do not include any numbers, symbols, or extra words like "Sure!", "Here are", "Keywords:", or other similar phrases.
#     3. Each tag must be from the provided TAGS_LIST without additional formatting.
#     4. Include all tags within TAGS_LIST that represent topics touched on within the excerpt.
#     5. DO NOT INCLUDE ANY NUMERATION, ADDITIONAL COMMENTS, OR ANY OTHER TEXT AT ALL. ONLY 1 KEYWORD PER INDEX AND NOTHING MORE
#     6. DO NOT PREPEND WITH 'KEYWORDS: ' OR ANY OTHER TEXT. ONLY PROVIDE THE LIST OF KEYWORDS.

#     The inferred question should be a complete sentence, as if someone had asked it directly, ending in a ?
#     The tags must exist in TAGS_LIST to be included in your response, and representative of some portion of the excerpt. 
#     Consider each tag in TAGS_LIST and carefully select the ones that represent some portion of information in the excerpt

#     Excerpt: {excerpt}
#     TAGS_LIST: {TAGS}

#     Please respond with the inferred question first, followed by a list (python list - []) of tags.

#     """

#     system_prompt = """
#     You are an expert assistant tasked with processing excerpts of video transcripts. These transcripts come from a YouTube live "Ask Me Anything" session where a doctor reads questions or comments from the carnivore diet community and responds to them. Your responsibility is to:
#     1. Accurately infer and generate a complete, coherent question based on the fragmented or unclear input at the beginning of the excerpt and the context provided by the doctor’s full response.
#     2. Identify relevant topics from the provided tags list that are representative of the content in the excerpt.

#     To achieve this:
#     1. Focus on reconstructing the most relevant question. The question must be complete, coherent, and inferred from the entirety of the transcript excerpt.
#     2. When producing the question, **only** output the inferred question as a standalone sentence. Do not include any additional text, explanation, labels, or preambles such as "Question:".
#     3. In the second task, output **only** a list of tags relevant to the excerpt. Each tag must be directly selected from the provided TAGS_LIST. Do not add any additional words, symbols, numeration, or explanations in your response.
#     4. Your responses must be formatted as follows:
#     - First, provide the inferred question.
#     - Immediately after, provide a list of tags (one per line) relevant to the excerpt, without any added text or comments.
#     5. Ensure that both the inferred question and the tags are based solely on the transcript excerpt provided and strictly adhere to the instructions.
# """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",  
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             temperature=0.2,
#             max_tokens=1500
#         )
#         logger.debug("Successfully received response from OpenAI.")
#         logger.info(f"response: {response}")
#     except Exception as e:
#         logger.error(f"Error in OpenAI API call: {e}")
#         raise e

#     output = response.choices[0].message.content.strip()
#     return output
    

# def process_data(json_data, output_dir="./2_added_qt", error_log_file="error_segments.json"):
#     """expected format: {'title': '...', 'body': 'question answer pair'}"""
    
#     sanitized_title = json_data[0]["title"].replace(" ", "_").replace("/", "_")  
#     output_dir = os.path.join(output_dir, f"PQT_{sanitized_title}.json")
    
#     if not os.path.exists(output_dir):
#         with open(output_dir, 'w') as f:
#             json.dump([], f)  

    
#     logger.info(f"Starting transcript processing for: {json_data[0]['title']}")

#     for idx, segment in enumerate(json_data):
#         body = segment["body"]
#         title = segment["title"]
#         try:
#             output = generate_question_tags(body)

#             try:
#                 # output must be split into question and tags list values
#                 output = output.split("?")
#                 output = [val.strip() for val in output]

#                 question = output[0] + "?"
#                 tags = [tag.strip() for tag in output[1].splitlines() if tag.strip()]

#                 logger.info(f"Successfully processed segment {idx}")
                
#                 segment["question"] = question
#                 segment["tags"] = tags
                
#                 with open(output_dir, 'r') as f:
#                     existing_data = json.load(f)

#                 existing_data.append(segment)

#                 with open(output_dir, 'w') as f:
#                     json.dump(existing_data, f, indent=2)

#                 logger.info(f"Segment appended to {output_dir}")

#             except Exception as e:
#                 logger.error(f"Error processing segment {idx}: {e}")
#                 write_failed_segment(idx, body, error_log_file)
#                 continue  

#         except Exception as e:
#             logger.error(f"Stopping processing of transcript due to error: {e}")
#             break

#     logger.info("Transcript processing complete.")


# def write_failed_segment(segment_index, body, error_log_file):
#     """
#     Write problematic segments to a JSON file for later review and rerun.
#     """
#     failed_segment = {"segment_index": segment_index, "body": body}

#     if os.path.exists(error_log_file):
#         with open(error_log_file, 'r+') as file:
#             error_data = json.load(file)
#             error_data.append(failed_segment)
#             file.seek(0)
#             json.dump(error_data, file, indent=2)
#     else:
#         with open(error_log_file, 'w') as file:
#             json.dump([failed_segment], file, indent=2)

#     logger.info(f"Segment {segment_index} written to {error_log_file} for later review.")


# def main(json_file_path):
#     logger.info(f"Loading data from file: {json_file_path}")

#     try:
#         with open(json_file_path, 'r') as f:
#             data = json.load(f)
#             logger.info(f"Successfully loaded data from transcript: {data[0]['title']}")
#     except FileNotFoundError:
#         logger.error(f"File not found: {json_file_path}")
#         sys.exit(1)
#     except json.JSONDecodeError:
#         logger.error(f"Error decoding JSON in file: {json_file_path}")
#         sys.exit(1)
#     except KeyError as e:
#         logger.error(f"Missing expected key {e} in the provided JSON file.")
#         sys.exit(1)

#     process_data(data)


# if __name__ == "__main__":
    
#     parser = argparse.ArgumentParser(description="Process YouTube transcripts and extract Q&A pairs using OpenAI.")
#     parser.add_argument("--json_file_path", "-f", type=str, help="The relative path to the JSON file containing the transcript.")
    
#     args = parser.parse_args()

#     json_file_path = args.json_file_path
#     main(json_file_path)

#     # data = {
#     # "title": "a_calorie_deficit_alone_will_not_work__here_s_why_______carnivore_q_a_march_19th__2024",
#     # "body": "what did you use what do you use for toothpaste also I don't have a gallbladder and sometimes struggle with digestion do you think chewing a mastic gum before meals will help Prime the stomach of for the meal thank you I don't really know what mastic gum is unfortunately but I also don't think you do need to um because you you're still going to make bile it's just not going to be stored in your gallbladder so it's just going to drip out constantly out of your liver and so if that's the case you just may not be able to eat a huge amount of of fatty you know fat at one time uh because it'll just won't get digested won't get absorbed really it'll get digested just won't be absorbed uh because you need bile to mul emulsify and put these into little my cells and those get taken into your lymphatics in in the form of chylomicrons and so if you're doing that uh with a with without a gallbladder you're just sort of constantly dripping out bile from your liver and so you just sort of need to eat smaller amounts of fat throughout the day and that will sort of catch that bile as it's coming out and before it gets reabsorbed so that's what you do a lot of people actually form what's called a pseudo gallbladder which is a an outpouching of the common bile duct and and it basically acts the same as a as a gallbladder and so those people can actually eat just like one meal a day or two meals a day if that's what they're you know the tickles are fancy andh and they don't have any problems with diarrhea so if you eat eat like a big steak with a lot of fat on it and you just eat to your body's desire and you just have to you know run to the bathroom after that you're probably not absorbing all that all that fat and so that could be what's going on there and so you just split up you split up those meals you still have the same amount you just sort of have a you know quarter of it now quarter of it in a couple hours quarter of it in a couple hours after that you just sort of split that up throughout the day as to oh as to toothpaste um I I sort of go back and forth sometimes I'll use baking soda um that's just you just wet the brush and dip it in some baking soda you brush your teeth with that just a bit of an abrasive you could just use a toothbrush a toothbrush is an abrasive but I don't I don't find that that's as good as baking soda I also now that I've been working with stone and spear Tallow um with my friend Asher they make it sort of a tooth powder and um it doesn't have all the weird you know micro Nano particles and weird you know sort of titanium white sort of stuff that's all and all these other sort of toothpastes as a as a coloring sort of thing uh it's just sort of like can bit them an abrasive and has some like sort of some of it has like a peppermint sort of flavor so I've been sort of using that too I tend to like things that don't have uh any any scents or flavors or anything like that so um baking soda is actually quite a good option baking soda actually is a bit abrasive so when you're that you sort of feel a bit you feel a bit raw in your mouth uh but it actually works really well and um so that's what I tend to use baking soda is great and then there's the these tooth powders and things like that that stone and spear make um that I've been using as well I tend to not use toothpaste just because of all the crap that they put in it not least of which is fluoride which I have no interest in and um and yeah and these these Nano particles that he's getting more and more uh weird information on that you know whether or not they do something bad to you it's like why why risk it like who cares you know it's not something you need you know you don't need it so why run the risk that it's you know that it's something that you don't need um or don't want so that's sort of my My Philosophy on that as well you know just avoid this crap you know there's all these oh well no there's this study and that study and this St who gives a you don't need it you know you don't need it so the potential for harm so why mess around you know you know in 50 years we get more robust data and be like yeah no we got long-term data this is totally safe fine you know but like right now we don't have that so you know why mess around"
#     # }
#     # generate_question_tags(data["body"])
