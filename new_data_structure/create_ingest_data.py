import os
import json
import argparse
from loguru import logger


def combine_json_files(directory, output_file="combined_output.json"):
    combined_data = []

    # Iterate over all files in the directory
    for file_name in os.listdir(directory):
        if file_name.endswith(".json"):
            file_path = os.path.join(directory, file_name)
            logger.info(f"Processing file: {file_path}")

            try:
                # Open and load the JSON data from the file
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Ensure the data is a list and extend the combined list with it
                if isinstance(data, list):
                    combined_data.extend(data)
                else:
                    logger.warning(f"File {file_path} does not contain a list of objects.")

            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON in file: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

    # Write the combined data to the output file
    with open(output_file, 'w') as outfile:
        json.dump(combined_data, outfile, indent=2)

    logger.info(f"Combined data saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine JSON files from a directory into one JSON file.")
    parser.add_argument("--dir", "-d", type=str, required=True, help="The path to the directory containing JSON files.")
    parser.add_argument("--output", "-o", type=str, default="second_ingest_data.json", help="The output JSON file.")

    args = parser.parse_args()

    if os.path.exists(args.dir) and os.path.isdir(args.dir):
        combine_json_files(args.dir, output_file=args.output)
    else:
        logger.error(f"Provided directory {args.dir} does not exist or is not a directory.")
