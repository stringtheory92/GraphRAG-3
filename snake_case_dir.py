import os
import re

def to_snake_case(filename):
    # Remove file extension
    name, ext = os.path.splitext(filename)
    
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces and special characters with underscores
    name = re.sub(r'[\s\W]+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # Add the extension back
    return f"{name}{ext}"

def rename_files_in_directory(directory):
    for filename in os.listdir(directory):
        # Check if the file is a JSON file
        if filename.endswith(".json"):
            snake_case_name = to_snake_case(filename)
            src = os.path.join(directory, filename)
            dst = os.path.join(directory, snake_case_name)
            
            # Rename the file
            os.rename(src, dst)
            print(f"Renamed: {filename} -> {snake_case_name}")

# Specify the directory where the JSON files are located
directory = "q&a_transcripts"


if __name__ == "__main__":
    # Run the renaming function
    rename_files_in_directory(directory)
