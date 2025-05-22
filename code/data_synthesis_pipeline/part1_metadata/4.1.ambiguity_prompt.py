import json
import os
from llm_gpt_call import call_gpt_4, call_gpt_3_5
import uuid
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

prompt = """You are an expert data analyst. Your task is to analyze the column names, their descriptions, and their example values to identify groups of columns that could be ambiguously referred to by a single natural language term, as well as columns that are unambiguous.

# Instructions:
1. Use the column names, descriptions, and example values to infer semantic relationships.
2. Group columns that are likely to be referred to by a single natural language term based on their names, descriptions, or the nature of their example values.
3. Avoid overgeneralizing; only group columns where ambiguity is reasonable.
4. Each ambiguity group should only include 2 or 3 columns. The natural language reference should be related specifically to those columns and not to other columns in the table.
5. Ensure that ambiguity groups are mutually exclusive - a column should only appear in one group. For example, instead of having "record": ["max_score", "min_score"] and "home_record": ["home_max_score", "home_min_score"], use more specific group names like "overall_record": ["max_score", "min_score"] and "home_record": ["home_max_score", "home_min_score"].
6. Identify columns that are unambiguous (not part of any ambiguity group).
7. Return the output in valid JSON format with two sections: "ambiguous_columns_groups" and "unambiguous_columns".

# Examples of ambiguous column groups and their natural language references:
- If the columns include "firstname" and "lastname", they could both be referred to as "name" in natural language.
- If the columns include "playername" and "playerid", they could be referred to as "player".
- {{"id": ["school_id", "room_id"]}}
- {{"location": ["province", "city"]}}
- {{"date": ["start_date", "end_date"]}}
- {{"address": ["street", "zipcode"]}}

# Example Input:
{{
  "columns": ["playername", "playerid", "city", "province", "score"],
  "values": {{
    "playername": ["Mike Jordan", "LeBron James"],
    "playerid": ["12345", "67890"],
    "city": ["Toronto", "Vancouver"],
    "province": ["Ontario", "British Columbia"],
    "score": ["98", "105"]
  }},
  "descriptions": {{
    "playername": "A text field containing the full name of the player",
    "playerid": "A unique identifier for each player in the system",
    "city": "The city where the game was played",
    "province": "The province or state where the game was played",
    "score": "The final score achieved by the player"
  }}
}}

# Example Output:
{{
  "ambiguous_columns_groups": {{
    "player": ["playername", "playerid"],
    "location": ["city", "province"]
  }},
  "unambiguous_columns": ["score"]
}}

Now, process the following input and provide the output:

# Input:
{0}

# Output:
"""


def extract_json_from_response(response):
    """
    Extract JSON from a response that might contain markdown code blocks or other formatting.
    
    Args:
        response: String containing a potential JSON response
        
    Returns:
        String containing only the JSON part of the response
    """
    import re
    
    # Check if the response contains a code block
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if code_block_match and code_block_match.group(1):
        return code_block_match.group(1).strip()
    
    # If no code block, try to find json-like content between braces
    braces_match = re.search(r'\{[\s\S]*\}', response)
    if braces_match:
        return braces_match.group(0)
    
    # Return the original if no patterns match
    return response

def process_table(args):
    """
    Process a single table to generate ambiguity pairs and unambiguous columns.
    
    Args:
        args: Tuple containing (table_name, table_data, output_dir, sys_content)
    
    Returns:
        tuple: (table_name, parsed_result) - Name of the processed table and its parsed result
    """
    table_name, table_data, output_dir, sys_content = args
    
    # Extract column names, descriptions, and example values
    columns = table_data["field_list"]
    examples = table_data["data_value_example"]
    descriptions = table_data.get("descriptions", {})
    
    # Format the input JSON
    input_data = {
        "columns": columns,
        "values": examples,
        "descriptions": descriptions
    }
    
    # Format the prompt with the input data
    user_content = prompt.format(json.dumps(input_data, indent=2))
    
    # Call GPT-4
    try:
        result, token_usage = call_gpt_4(user_content, sys_content)
    except Exception as e:
        print(f"Error calling GPT for table {table_name}: {e}")
        return table_name, None
    
    # Extract JSON from the result (handles markdown code blocks)
    cleaned_result = extract_json_from_response(result)
    
    # Try to parse the cleaned result as JSON
    try:
        parsed_result = json.loads(cleaned_result)
    except json.JSONDecodeError:
        parsed_result = {
            "ambiguous_columns_groups": {},
            "unambiguous_columns": []
        }
        print(f"Failed to parse GPT output for table {table_name}")
    
    # Prepare output data
    output_data = {
        "table_name": table_name,
        "original_response": result,
        "parsed_response": parsed_result,
        "token_usage": token_usage
    }
    
    # Save to file
    output_file = os.path.join(output_dir, f"{table_name}.csv.json")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
    except Exception as e:
        print(f"Error saving results for {table_name}: {e}")
    
    return table_name, parsed_result

def generate_ambiguity_pairs(metadata, output_dir="./llm_ambiguity_pairs"):
    """
    Generate ambiguity pairs and unambiguous columns for each table using GPT-4 and save results.
    Uses multiprocessing for parallel execution.
    
    Args:
        metadata: Dictionary containing table metadata with descriptions
        output_dir: Directory to save output JSON files
    
    Returns:
        Dictionary: Updated metadata with ambiguity information
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # System content for GPT
    sys_content = "You are an expert data analyst. Provide the output in valid JSON format as specified in the prompt."
    
    # Prepare arguments for multiprocessing
    process_args = [
        (table_name, table_data, output_dir, sys_content)
        for table_name, table_data in metadata.items()
    ]
    
    # Determine number of workers (use at most 75% of available cores)
    max_workers = max(1, int(multiprocessing.cpu_count() * 0.75))
    
    # Process tables in parallel with progress bar and collect results
    results = {}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for table_name, parsed_result in tqdm(
            executor.map(process_table, process_args),
            total=len(process_args),
            desc="Processing tables"
        ):
            if parsed_result is not None:
                results[table_name] = parsed_result
    
    # Update metadata with ambiguity information
    metadata_with_ambiguity = {}
    for table_name, table_data in metadata.items():
        metadata_with_ambiguity[table_name] = table_data.copy()
        if table_name in results:
            metadata_with_ambiguity[table_name]["ambiguous_columns_groups"] = results[table_name].get("ambiguous_columns_groups", {})
            metadata_with_ambiguity[table_name]["unambiguous_columns"] = results[table_name].get("unambiguous_columns", [])
    
    # Save the combined metadata file
    with open("BIRD_metadata_w_ambiguity.json", "w", encoding="utf-8") as f:
        json.dump(metadata_with_ambiguity, f, indent=2)
    
    return metadata_with_ambiguity

if __name__ == "__main__":
    # Load the BIRD metadata with descriptions
    try:
        with open("BIRD_metadata_w_description.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print("BIRD_metadata_w_description.json not found")
        exit(1)
    except json.JSONDecodeError:
        print("Error decoding BIRD_metadata_w_description.json")
        exit(1)
    
    # Generate ambiguity pairs, unambiguous columns, and save results
    updated_metadata = generate_ambiguity_pairs(metadata)
    print(f"Saved combined metadata to BIRD_metadata_w_ambiguity.json")