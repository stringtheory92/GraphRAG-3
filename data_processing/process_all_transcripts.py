# import os
# import re
# import json

# def load_transcript(file_path):
#     """Loads the transcript from the provided JSON file."""
#     with open(file_path, 'r') as f:
#         transcript_data = json.load(f)
#     return transcript_data

# def process_transcript(transcript, title, overlap_chars=55):
#     """Processes the transcript by splitting it into segments based on 'super chat' with overlap."""
#     # Find the positions of "super chat" in the text (case insensitive)
#     positions = [(m.start(), m.end()) for m in re.finditer(r'\bsuper chat\b', transcript, flags=re.IGNORECASE)]

#     # If there are no "super chat" occurrences, return the entire transcript as one topic
#     if not positions:
#         return [{"title": title, "transcript": transcript}]

#     # Prepare list to hold transcript sections
#     sections = []
#     start_idx = 0

#     for start, end in positions:
#         # Get the portion of the transcript leading up to 'super chat', plus 55 chars before it
#         pre_super_chat = max(start - overlap_chars, 0)  # Ensure we don't go negative
#         section = transcript[start_idx:pre_super_chat].strip()
#         if section:
#             sections.append({"title": title, "transcript": section})

#         # Set the next start index, making sure to include 55 characters after 'super chat'
#         start_idx = max(start - overlap_chars, 0)

#     # Add the final section (after the last "super chat")
#     sections.append({"title": title, "transcript": transcript[start_idx:].strip()})

#     # Include the 55-character overlap for each section
#     for i in range(len(sections) - 1):
#         overlap = transcript[positions[i][0] - overlap_chars : positions[i][0]].strip()
#         sections[i]['transcript'] += ' ' + overlap
#         sections[i + 1]['transcript'] = overlap + ' ' + sections[i + 1]['transcript']

#     return sections

# def save_to_json(sections, output_path):
#     """Saves the processed sections to a JSON file."""
#     with open(output_path, "w") as f:
#         json.dump(sections, f, indent=4)

# def process_directory(input_dir, output_dir):
#     """Processes all JSON files in the input directory and outputs processed files to the output directory."""
#     # Ensure the output directory exists
#     os.makedirs(output_dir, exist_ok=True)

#     # Loop through all JSON files in the input directory
#     for file_name in os.listdir(input_dir):
#         if file_name.endswith(".json"):
#             input_file_path = os.path.join(input_dir, file_name)
#             print(f"Processing file: {input_file_path}")

#             # Load the transcript from the JSON file
#             transcript_data = load_transcript(input_file_path)

#             # Extract the title and transcript content
#             title = transcript_data["title"]
#             transcript_text = transcript_data["transcript"]

#             # Process the transcript
#             sections = process_transcript(transcript_text, title)

#             # Define the output file path
#             output_file_name = file_name.replace(".json", "_processed.json")
#             output_file_path = os.path.join(output_dir, output_file_name)

#             # Save the processed sections to a new JSON file
#             save_to_json(sections, output_file_path)

#             print(f"Saved processed file to: {output_file_path}")

# # Example usage:
# # Specify the input and output directories
# input_directory = "test_transcripts"
# output_directory = "batched_processed_files"
# # output_directory = "data_processing/batch_processed_files"

# # Process all JSON files in the input directory
# process_directory(input_directory, output_directory)

# ** OLD VERSION ABOVE - TRIES TO SPLIT EVERY FILE BY 'super chat', LOADS EVERY FILE INTO OUTPUT DIR

# ** NEW VERSION BELOW - IF FILE DOES NOT CONTAIN 'super chat', DOES NOTHING - INTENDED TO EXTEND FUNCTIONALITY FOR MORE VIDEO TYPES


import os
import re
import json

def load_transcript(file_path):
    """Loads the transcript from the provided JSON file."""
    with open(file_path, 'r') as f:
        transcript_data = json.load(f)
    return transcript_data

def process_transcript(transcript, title, overlap_chars=55):
    """Processes the transcript by splitting it into segments based on 'super chat' with overlap."""
    # Find the positions of "super chat" in the text (case insensitive)
    positions = [(m.start(), m.end()) for m in re.finditer(r'\bsuper chat\b', transcript, flags=re.IGNORECASE)]

    # If there are no "super chat" occurrences, return an empty list (no processing needed)
    if not positions:
        return []

    # Prepare list to hold transcript sections
    sections = []
    start_idx = 0

    for start, end in positions:
        # Get the portion of the transcript leading up to 'super chat', plus 55 chars before it
        pre_super_chat = max(start - overlap_chars, 0)  # Ensure we don't go negative
        section = transcript[start_idx:pre_super_chat].strip()
        if section:
            sections.append({"title": title, "transcript": section})

        # Set the next start index, making sure to include 55 characters after 'super chat'
        start_idx = max(start - overlap_chars, 0)

    # Add the final section (after the last "super chat")
    sections.append({"title": title, "transcript": transcript[start_idx:].strip()})

    # Include the 55-character overlap for each section
    for i in range(len(sections) - 1):
        overlap = transcript[positions[i][0] - overlap_chars : positions[i][0]].strip()
        sections[i]['transcript'] += ' ' + overlap
        sections[i + 1]['transcript'] = overlap + ' ' + sections[i + 1]['transcript']

    return sections

def save_to_json(sections, output_path):
    """Saves the processed sections to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(sections, f, indent=4)

def process_directory(input_dir, output_dir):
    """Processes all JSON files in the input directory and outputs processed files to the output directory."""
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Loop through all JSON files in the input directory
    for file_name in os.listdir(input_dir):
        if file_name.endswith(".json"):
            input_file_path = os.path.join(input_dir, file_name)
            print(f"Processing file: {input_file_path}")

            # Load the transcript from the JSON file
            transcript_data = load_transcript(input_file_path)

            # Extract the title and transcript content
            title = transcript_data["title"]
            transcript_text = transcript_data["transcript"]

            # Check if the transcript contains "super chat"
            if "super chat" not in transcript_text.lower():
                print(f"'super chat' not found in {file_name}. Skipping file.")
                continue

            # Process the transcript if "super chat" is found
            sections = process_transcript(transcript_text, title)

            # If sections were generated, save to a JSON file
            if sections:
                output_file_name = file_name.replace(".json", "_processed.json")
                output_file_path = os.path.join(output_dir, output_file_name)

                # Save the processed sections to a new JSON file
                save_to_json(sections, output_file_path)

                print(f"Saved processed file to: {output_file_path}")

# Example usage:
# Specify the input and output directories
input_directory = "test_transcripts"
output_directory = "data_processing/batched_processed_files"

# Process all JSON files in the input directory
process_directory(input_directory, output_directory)
