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

    # If there are no "super chat" occurrences, return the entire transcript as one topic
    if not positions:
        return [{"title": title, "transcript": transcript}]

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

def save_to_json(sections, filename="processed_transcript.json"):
    """Saves the processed sections to a JSON file in the 'processed_files' directory."""
    # Ensure the 'processed_files' directory exists
    output_dir = "processed_files"
    os.makedirs(output_dir, exist_ok=True)

    # Define the full path for the output JSON file
    output_path = os.path.join(output_dir, filename)

    # Save the processed sections to the JSON file
    with open(output_path, "w") as f:
        json.dump(sections, f, indent=4)

    print(f"Processed transcript saved to {output_path}")

# Example usage:
transcript_file_path = "test_transcripts/Ask_Me_Anything_with_Dr_Anthony_Chaffee_April_28_2023.json"


# Load the transcript from the JSON file
transcript_data = load_transcript(transcript_file_path)

# Extract the title and transcript content
title = transcript_data["title"]
transcript_text = transcript_data["transcript"]

# Process the transcript and get the separated sections with 55-character overlap
sections = process_transcript(transcript_text, title)

# Save the sections to a JSON file in the 'processed_files' directory
save_to_json(sections, "Ask_Me_Anything_April_28_2023_processed.json")
