import os
import re
import json
import argparse
from loguru import logger

# Set up logging
logger.add("transcript_processing.log", rotation="1 MB")

def snake_case_title(title):
    """Converts a title to snake_case."""
    title_snake_case = re.sub(r'[\W]+', '_', title.lower())
    logger.info(f"Converted title to snake_case: {title_snake_case}")
    return title_snake_case

def load_transcript(file_path):
    """Loads the transcript from the provided JSON file."""
    logger.info(f"Loading transcript from {file_path}")
    try:
        with open(file_path, 'r') as f:
            transcript_data = json.load(f)
        return transcript_data
    except Exception as e:
        logger.error(f"Error loading transcript: {e}")
        raise

def process_transcript(transcript, title, overlap_chars=55):
    """Processes the transcript by splitting it into segments based on 'super chat' with overlap."""
    logger.info("Processing transcript")
    positions = [(m.start(), m.end()) for m in re.finditer(r'\bsuper chat\b', transcript, flags=re.IGNORECASE)]

    if not positions:
        logger.warning("No 'super chat' occurrences found, returning entire transcript as one topic")
        return [{"title": snake_case_title(title), "body": transcript}]

    sections = []
    start_idx = 0

    for start, end in positions:
        pre_super_chat = max(start - overlap_chars, 0)
        section = transcript[start_idx:pre_super_chat].strip()
        if section:
            sections.append({"title": snake_case_title(title), "body": section})
        start_idx = max(start - overlap_chars, 0)

    sections.append({"title": snake_case_title(title), "body": transcript[start_idx:].strip()})

    for i in range(len(sections) - 1):
        overlap = transcript[positions[i][0] - overlap_chars : positions[i][0]].strip()
        sections[i]['body'] += ' ' + overlap
        sections[i + 1]['body'] = overlap + ' ' + sections[i + 1]['body']

    logger.info(f"Transcript processed into {len(sections)} sections")
    return sections

def save_to_json(sections, filename):
    """Saves the processed sections to a JSON file in the 'processed_files' directory."""
    output_dir = "processed_files"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    try:
        with open(output_path, "w") as f:
            json.dump(sections, f, indent=4)
        logger.info(f"Processed transcript saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving processed transcript: {e}")
        raise

def process_single_file(file_path, overlap_chars=55, output=None):
    """Process a single transcript file."""
    try:
        transcript_data = load_transcript(file_path)
        title = transcript_data.get("title", "Untitled Transcript")
        transcript_text = transcript_data["transcript"]

        # Convert title to snake_case
        title_snake_case = snake_case_title(title)

        # If no output name is given, use the snake_cased title
        output_filename = output if output else f"{title_snake_case}.json"

        sections = process_transcript(transcript_text, title, overlap_chars)
        save_to_json(sections, output_filename)
    except Exception as e:
        logger.error(f"Failed to process transcript: {e}")

def process_directory(directory, overlap_chars=55):
    """Process all JSON transcript files in a directory."""
    logger.info(f"Processing all files in directory: {directory}")
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            logger.info(f"Processing file: {file_path}")
            process_single_file(file_path, overlap_chars)

def main(args):
    if args.directory:
        process_directory(args.directory, args.overlap)
    elif args.f:
        process_single_file(args.f, args.overlap, args.output)
    else:
        logger.error("You must provide either a file (-f) or a directory (--directory)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON transcript or a directory of JSON transcripts and split them by 'super chat'.")
    parser.add_argument("-f", help="Path to the input JSON transcript file")
    parser.add_argument("--directory", help="Path to the directory containing JSON transcript files")
    parser.add_argument("--overlap", type=int, default=55, help="Number of characters to overlap around 'super chat' (default: 55)")
    parser.add_argument("--output", help="Name of the output JSON file (default: snake_case title)")
    args = parser.parse_args()
    main(args)



# import os
# import re
# import json
# import argparse
# from loguru import logger

# # Set up logging
# logger.add("transcript_processing.log", rotation="1 MB")

# def snake_case_title(title):
#     """Converts a title to snake_case."""
#     title_snake_case = re.sub(r'[\W]+', '_', title.lower())
#     logger.info(f"Converted title to snake_case: {title_snake_case}")
#     return title_snake_case

# def load_transcript(file_path):
#     """Loads the transcript from the provided JSON file."""
#     logger.info(f"Loading transcript from {file_path}")
#     try:
#         with open(file_path, 'r') as f:
#             transcript_data = json.load(f)
#         return transcript_data
#     except Exception as e:
#         logger.error(f"Error loading transcript: {e}")
#         raise

# def process_transcript(transcript, title, overlap_chars=55):
#     """Processes the transcript by splitting it into segments based on 'super chat' with overlap."""
#     logger.info("Processing transcript")
#     positions = [(m.start(), m.end()) for m in re.finditer(r'\bsuper chat\b', transcript, flags=re.IGNORECASE)]

#     if not positions:
#         logger.warning("No 'super chat' occurrences found, returning entire transcript as one topic")
#         return [{"title": snake_case_title(title), "body": transcript}]

#     sections = []
#     start_idx = 0

#     for start, end in positions:
#         pre_super_chat = max(start - overlap_chars, 0)
#         section = transcript[start_idx:pre_super_chat].strip()
#         if section:
#             sections.append({"title": snake_case_title(title), "body": section})
#         start_idx = max(start - overlap_chars, 0)

#     sections.append({"title": snake_case_title(title), "body": transcript[start_idx:].strip()})

#     for i in range(len(sections) - 1):
#         overlap = transcript[positions[i][0] - overlap_chars : positions[i][0]].strip()
#         sections[i]['body'] += ' ' + overlap
#         sections[i + 1]['body'] = overlap + ' ' + sections[i + 1]['body']

#     logger.info(f"Transcript processed into {len(sections)} sections")
#     return sections

# def save_to_json(sections, filename):
#     """Saves the processed sections to a JSON file in the 'processed_files' directory."""
#     output_dir = "processed_files"
#     os.makedirs(output_dir, exist_ok=True)
#     output_path = os.path.join(output_dir, filename)

#     try:
#         with open(output_path, "w") as f:
#             json.dump(sections, f, indent=4)
#         logger.info(f"Processed transcript saved to {output_path}")
#     except Exception as e:
#         logger.error(f"Error saving processed transcript: {e}")
#         raise

# def main(args):
#     try:
#         transcript_data = load_transcript(args.f)
#         title = transcript_data.get("title", "Untitled Transcript")
#         transcript_text = transcript_data["transcript"]

#         # Convert title to snake_case
#         title_snake_case = snake_case_title(title)

#         # If no output name is given, use the snake_cased title
#         output_filename = args.output if args.output else f"{title_snake_case}.json"

#         sections = process_transcript(transcript_text, title, args.overlap)
#         save_to_json(sections, output_filename)
#     except Exception as e:
#         logger.error(f"Failed to process transcript: {e}")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Process a JSON transcript and split it by 'super chat'.")
#     parser.add_argument("-f", help="Path to the input JSON transcript file")
#     parser.add_argument("--overlap", type=int, default=55, help="Number of characters to overlap around 'super chat' (default: 55)")
#     parser.add_argument("--output", help="Name of the output JSON file (default: snake_case title)")
#     args = parser.parse_args()
#     main(args)
