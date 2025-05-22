import json
import os

def join_json_files(directory: str = "./vis_output_0224/") -> dict:
    combined_data = {}
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as f:
                data = json.load(f)
                combined_data[filename] = data

    return combined_data

# Example usage
if __name__ == "__main__":
    all_data = join_json_files()
    with open("output_combine.json", "w") as outfile:
        json.dump(all_data, outfile, indent=2)