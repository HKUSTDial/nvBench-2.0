import ast
import os
import json
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from llm_gpt_call import call_gpt_3_5, call_gpt_4

sys_content = "You are an intelligent assistant."
prompt = """#Task: Generate 3 Natural Language Query for a data-to-chart problem based on a given Data Schema and Action List.

The 3 NL Queries are of types:
- command (e.g. visualize data/plot relationship/show correlation/give a chart of/use bars to/use lines to/show points of/trending lines/histogram/)
- question (e.g. What is the relationship between movie's ticket price and rating? explain with a line chart.)
- statement (e.g. Distribution of count by product in pie.)

## Input Action List Format:
The input action_list may contain the following operations:
- "mark chart_type" - specifies the visualization type
- "column column_name" - selects a data column
- "bin bin_size column_name" - groups data into bins or time units of specified size
- "aggregation para column_name" - performs aggregation operation (sum, average, count, etc.)
- "sort order column_name" - sorts data by specified column and order
- "filter column_name operation value" - filters data based on condition

## Special Notation:
If a column_name is tagged with [AMBI], it indicates the NL Query should include an ambiguous phrase. 
Example: action "column [AMBI]name" might be phrased as "What are the names of highest score players?" where the data schema only has "last_name" or "first_name" columns, not a general "name" column.

## Requirements:
- Each NL Query MUST incorporate ALL information from the INPUT action_list
- NL Queries MUST NOT introduce extra information NOT in the input action_list
- Use natural language rather than technical terms (avoid "aggregation", "filter", "bin", etc.)
- Use common prepositions (over, above, etc.) instead of technical terms like "larger than"
- For data columns, you should use semantic references that don't introduce ambiguity (e.g., "player" can refer to "name" column in a football player table)
- If a column is NOT tagged as [AMBI], use appropriate synonyms without introducing ambiguity (e.g., "last_name" can be phrased as "family name" but not just "name")
- You may use different alias to name a chart, especially when some action exist jointly. For example:
-- Bar Chart = [column chart, histogram (when showing frequency distribution), ranged bar chart(when x is binned), horizontal bar chart]
-- Scatter Plot = [point chart, dot plot, scattergram, correlation points]
-- Heatmap = [color matrix, density plot, heat grid, thermal map, correlation matrix (for variables)]
-- Boxplot = [range plot, box distribution, ...]
etc.

## Output Format:
#OUTPUT: {
  "command": "",
  "question": "",
  "statement": ""
}

#INPUT: """



input_dir = "../part2.vis_asp/nl_generation_input_multiprocess"
output_dir = "./nl_generation_output_gpt_35_0227"

# Make sure the output directory exists
os.makedirs(output_dir, exist_ok=True)

def process_file(json_file):
    output_file_path = os.path.join(output_dir, json_file)
    if os.path.exists(output_file_path):
        return None  # Skip if output already exists
    basename = os.path.basename(json_file)
        
    with open(os.path.join(input_dir, json_file), 'r') as file:
        json_dict = json.load(file)
    
    save_dict = {}
    for s_idx, solution in json_dict.items():
        action_list = solution["action_list"]
        data_schema = solution["data_schema"]
        ambiguous_pairs = solution["ambiguous_pairs"]
        data_value_example = solution["data_value_example"]
        info = f"""\nDatabase: {basename}\nData Columns: {data_schema}\nData Value Examples:{data_value_example}\nAmbiguous Column Pairs:{ambiguous_pairs}\nAction List:{action_list}"""
        input_str = prompt + info

        # print(input_str)
        # exit()
        
        # if "[AMBI]" in input_str:
        #     input_str = input_str.replace("[AMBI]", "")
        
        # Call GPT
        result, token_usage = call_gpt_3_5(input_str, sys_content)
        # result, token_usage = call_gpt_4(input_str, sys_content)
        
        save_dict[s_idx] = solution
        nl_query_list_str = result.split("#OUTPUT:")[1]
        
        try:
            nl_query_list = ast.literal_eval(nl_query_list_str)
            save_dict[s_idx]["nl_query_list"] = nl_query_list
        except Exception as e:
            print(f"Error parsing result for {json_file}, solution {s_idx}: {e}")
            # Provide a fallback or handle the error appropriately
            save_dict[s_idx]["nl_query_list"] = {"error": str(result)}
    
    # Write results to output file
    with open(output_file_path, 'w') as output_file:
        json.dump(save_dict, output_file, indent=4)
    
    return json_file

def main():
    # Get list of files to process
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    files_to_process = []
    
    for json_file in json_files:
        output_file_path = os.path.join(output_dir, json_file)
        if not os.path.exists(output_file_path):
            files_to_process.append(json_file)
    
    print(f"Found {len(files_to_process)} files to process out of {len(json_files)} total")
    
    # Maximum number of workers
    max_workers = min(os.cpu_count(), 8)  # Limit to 8 or CPU count, whichever is smaller
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_file, json_file): json_file for json_file in files_to_process}
        
        # Process as they complete
        for future in tqdm(as_completed(future_to_file), total=len(files_to_process), desc="Processing files"):
            json_file = future_to_file[future]
            try:
                result = future.result()
                if result:
                    print(f"Processed: {result}")
            except Exception as e:
                print(f"Error processing {json_file}: {e}")

if __name__ == "__main__":
    main()