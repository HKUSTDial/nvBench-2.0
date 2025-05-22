import json
import os
from llm_gpt_call import call_gpt_4, call_gpt_3_5
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import copy

prompt = """You are an expert data analyst. Your task is to provide clear, concise descriptions for all columns in a database table based on their names and example values.

# Instructions:
1. Analyze each column name and its example values to understand the data type and purpose.
2. Provide a brief (1-2 sentences) description for each column that explains what it represents.
3. Include information about the data type and format if relevant.
4. Be specific but concise.

# Example Input:
{{
  "table_name": "patients",
  "columns": {{
    "birthdate": ["1928-04-12", "1921-10-11", "1930-04-10"],
    "gender": ["F", "M", "F"],
    "patient_id": ["P12345", "P67890", "P24680"]
  }}
}}

# Example Output:
{{
  "birthdate": "A date field representing a person's date of birth in YYYY-MM-DD format.",
  "gender": "A categorical field indicating the patient's gender, with values like 'F' for female and 'M' for male.",
  "patient_id": "A unique identifier for each patient, starting with 'P' followed by a numeric sequence."
}}

Now, provide descriptions for all columns in the following table:

# Input:
{0}

# Output:
"""

def extract_json_from_response(response):
    """
    Extract JSON from a response that might contain markdown code blocks or other formatting.
    Raises json.JSONDecodeError if parsing fails.
    
    Args:
        response: String containing a potential JSON response
        
    Returns:
        Dictionary containing the parsed JSON
    """
    import re
    
    # Check if the response contains a code block
    code_block_match = re.search(r'```(?:json)?\s*([^\s\S]*?)\s*```', response)
    if code_block_match and code_block_match.group(1):
        json_str = code_block_match.group(1).strip()
    else:
        # If no code block, try to find json-like content between braces
        braces_match = re.search(r'\{[^\s\S]*\}|[^\s\S]*', response)
        if braces_match:
            json_str = braces_match.group(0)
        else:
            # If no clear JSON structure is found, assume the whole response might be JSON
            # This might raise an error if the response is not valid JSON, which is now intended
            json_str = response
    
    # Try to parse the JSON - will raise JSONDecodeError if invalid
    return json.loads(json_str)

def process_table(args):
    """
    Process a single table to generate descriptions for all its columns.
    
    Args:
        args: Tuple containing (table_name, table_data, output_dir, sys_content)
    
    Returns:
        tuple: (table_name, column_descriptions)
    """
    table_name, table_data, output_dir, sys_content = args
    
    # Extract column names and example values
    columns = table_data["field_list"]
    examples = table_data["data_value_example"]
    
    # Format the input JSON
    input_data = {
        "table_name": table_name,
        "columns": examples
    }
    
    # Format the prompt with the input data
    json_str = json.dumps(input_data, indent=2)
    user_content = prompt.format(json_str)
    
    # Call GPT
    try:
        # result, token_usage = call_gpt_3_5(user_content, sys_content)
        # Fallback to GPT-4 if needed
        result, token_usage = call_gpt_4(user_content, sys_content)
    except Exception as e:
        print(f"Error calling GPT for table {table_name}: {e}")
        return table_name, {}
    
    # Extract descriptions from the result
    try:
        descriptions = extract_json_from_response(result)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response for table '{table_name}'. Error: {e}")
        print(f"Original response content:\n{result}") # Log the response that failed
        return table_name, {} # Return empty dict for this table on parsing failure
    
    # Prepare output data
    output_data = {
        "table_name": table_name,
        "descriptions": descriptions,
        "original_response": result,
        "token_usage": token_usage
    }
    
    # Save to file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{table_name}.json")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
    except Exception as e:
        print(f"Error saving results for {table_name}: {e}")
    
    return table_name, descriptions

def generate_column_descriptions(metadata, output_dir="./llm_column_descriptions"):
    """
    Generate descriptions for all columns in each table using LLM and save results.
    Uses multiprocessing for parallel execution.
    
    Args:
        metadata: Dictionary containing table metadata
        output_dir: Directory to save output JSON files
        
    Returns:
        Dictionary containing all table metadata with added column descriptions
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # System content for GPT
    sys_content = "You are an expert data analyst. Provide clear, concise descriptions for database columns."
    
    # Prepare arguments for multiprocessing
    process_args = [
        (table_name, table_data, output_dir, sys_content)
        for table_name, table_data in metadata.items()
    ]
    
    # Determine number of workers (use at most 75% of available cores)
    max_workers = max(1, int(multiprocessing.cpu_count() * 0.75))
    
    # Process tables in parallel with progress bar
    results = {}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for table_name, descriptions in tqdm(
            executor.map(process_table, process_args),
            total=len(process_args),
            desc="Processing tables"
        ):
            results[table_name] = descriptions
    
    # Save consolidated results
    with open(os.path.join(output_dir, "all_descriptions.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # Create a deep copy of the metadata to avoid modifying the original
    metadata_with_descriptions = copy.deepcopy(metadata)
    
    # Add descriptions to the metadata
    for table_name, descriptions in results.items():
        if table_name in metadata_with_descriptions:
            metadata_with_descriptions[table_name]["column_description"] = descriptions
    
    return metadata_with_descriptions

if __name__ == "__main__":
    # Load the BIRD metadata
    try:
        with open("BIRD_metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print("BIRD_metadata.json not found")
        exit(1)
    except json.JSONDecodeError:
        print("Error decoding BIRD_metadata.json")
        exit(1)
    
    # Generate column descriptions and save results
    metadata_with_descriptions = generate_column_descriptions(metadata)
    
    # Save the updated metadata to a new file
    try:
        with open("BIRD_metadata_w_description.json", "w", encoding="utf-8") as f:
            json.dump(metadata_with_descriptions, f, indent=2)
        print("Successfully saved BIRD_metadata_w_description.json")
    except Exception as e:
        print(f"Error saving BIRD_metadata_w_description.json: {e}")


