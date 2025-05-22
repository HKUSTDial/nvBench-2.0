import ast
from llm_gpt_call import call_gpt_3_5, call_gpt_4
sys_content = "You are an intelligent assistant. You only answer with #OUTPUT."
prompt = """#Task: generate 4 different Natural Language Queries for the data-to-chart problem, as command(plot/show/etc.), question(what/how/etc.), requirement(please/can you/etc.), statement(I want/I'd like/lets/etc.), etc. action_list may have "mark chart_type", "column column_name", "bin bin_size column_name", "aggregation para column_name", "sort order column_name", "filter column_name operation value". Since it's natural language query, do not refer to column_name = 'name' as column 'name', just as name.
Every the NL Queries MUST reflect ALL information in the INPUT action_list, but MUST NOT introduce extra information NOT in input action_list.
Please output in format #OUTPUT: {"command": "", "question": "", "requirement": "", "statement": ""}
#INPUT: """

import os
import json

input_dir = "./nl_generation_input"
output_dir = "./nl_generation_output_gpt_35"

from tqdm import tqdm

for json_file in tqdm(os.listdir(input_dir)):
    output_file_path = os.path.join(output_dir, json_file)
    if os.path.exists(output_file_path):
        continue

    with open(os.path.join(input_dir, json_file), 'r') as file:
        json_dict = json.load(file)

    save_dict = {}
    for s_idx, solution in json_dict.items():
    
        action_list = {"action_list": solution["action_list"]}
        input_str = prompt + str(action_list)

        if "[AMBI]" in input_str:
            input_str = input_str.replace("[AMBI]", "")

        # print(input_str)
        # Call GPT
        # result, token_usage = call_gpt_4(input_str, sys_content)
        result, token_usage = call_gpt_3_5(input_str, sys_content)
        # print("Result:", result)
        # exit()

        save_dict[s_idx] = solution
        nl_query_list_str = result.split("#OUTPUT:")[1]
        
        nl_query_list = ast.literal_eval(nl_query_list_str)
        save_dict[s_idx]["nl_query_list"] =  nl_query_list

    
    with open(output_file_path, 'w') as output_file:
        json.dump(save_dict, output_file, indent=4)

