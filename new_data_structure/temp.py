import re
from loguru import logger


logger.info("Start")
# Path to your JSON file
json_file_path = 'ingest_data.json'

# Function to replace single quotes around tags, except for known issues like "Alzheimer's"
def replace_single_quotes_in_tags(json_string):
    # Regular expression to find "tags": ['...'] and replace single quotes around each tag
    fixed_json_string = re.sub(r'"tags": \[(.*?)\]', 
        lambda match: '"tags": [' + ', '.join(
            f'"{tag.strip()[1:-1]}"' if tag.strip().startswith("'") and tag.strip().endswith("'") and "Alzheimer's" not in tag else tag
            for tag in match.group(1).split(',')) + ']', 
        json_string)

    # Log the changes
    if fixed_json_string != json_string:
        logger.info("Changes detected and fixed.")
    else:
        logger.info("No changes detected.")

    return fixed_json_string

# Read the JSON file as a string (even though it's invalid)
try:
    with open(json_file_path, 'r') as f:
        json_content = f.read()
    logger.info(f"Successfully read {json_file_path}")
except Exception as e:
    logger.error(f"Error reading file: {e}")
    exit(1)

# Log before fixing
logger.debug("Before fixing:")
logger.debug(json_content)

# Fix only single quotes around tags in the "tags" key, while handling "Alzheimer's" case
fixed_json_content = replace_single_quotes_in_tags(json_content)

# Log after fixing
logger.debug("After fixing:")
logger.debug(fixed_json_content)

# Write the fixed content back to the JSON file
try:
    with open(f"2{json_file_path}", 'w') as f:
        f.write(fixed_json_content)
    logger.info(f"Fixed single quotes and updated {json_file_path} successfully.")
except Exception as e:
    logger.error(f"Error writing to file: {e}")
    exit(1)