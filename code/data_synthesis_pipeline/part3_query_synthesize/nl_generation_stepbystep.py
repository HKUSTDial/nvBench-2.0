import ast
import os
import json
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from llm_gpt_call import call_gpt_3_5, call_gpt_4
from nl_prompt import step_prompt
from utils.print_utils import suppress_stdout

sys_content = "You are an intelligent assistant."
prompt = step_prompt

input_dir = "../part2.vis_asp/nl_generation_input_multiprocess"
output_dir = "./nl_generation_output_gpt_35_stepbystep"

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
        save_dict[s_idx]["nl_generate_gpt_result_full"] = result

        nl_query_list_str = result.split("## Final Output:")[1]

        save_dict[s_idx]["nl_query_list_str"] = nl_query_list_str
        
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
    
    with suppress_stdout():
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
                    with suppress_stdout():
                        print(f"Processed: {result}")
            except Exception as e:
                with suppress_stdout():
                    print(f"Error processing {json_file}: {e}")

if __name__ == "__main__":
    main()