import os
import json
import random
import pandas as pd
import numpy as np
from tqdm import tqdm  # Import tqdm for progress tracking

# Set directories
csv_dir = "../part1.nvbench_tables/database_csv"
output_dir = "./vis_output_multiprocess/"

# save by csv_filename
save_dir = "./nl_generation_input_multiprocess/"

# # Check if the directory exists
# if os.path.exists(save_dir):
#     raise FileExistsError(f"The directory '{save_dir}' already exists.")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)  # Create the directory if it does not exist
else:
    raise FileExistsError(f"The directory '{save_dir}' already exists.")


# load "nvbench_metadata.json"
nvbench_metadata_path = "../part1.nvbench_tables/nvbench_metadata.json"
with open(nvbench_metadata_path, 'r') as metadata_file:
    all_metadata = json.load(metadata_file)

def convert_int64_to_int(data):
    if isinstance(data, dict):
        return {key: convert_int64_to_int(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_int64_to_int(item) for item in data]
    elif isinstance(data, np.int64):  # Assuming you are using NumPy
        return int(data)
    return data

def get_info_by_field(csv_path):
    df = pd.read_csv(csv_path)
    info_by_field = {}

    for column in df.columns:
        unique_values = sorted(df[column].dropna().unique()) 
        # print(unique_values)

        info_by_field[column] = {
            "unique_values": unique_values, 
            "min": None,
            "max": None
        }

        if len(unique_values) == 0:
            continue
        # Determine the type of the column based on unique values
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            info_by_field[column]["min"] = unique_values[0]
            info_by_field[column]["max"] = unique_values[-1]
        elif pd.api.types.is_numeric_dtype(df[column]):
            info_by_field[column]["min"] = unique_values[0]
            info_by_field[column]["max"] = unique_values[-1]
        else:
            info_by_field[column]["min"] = unique_values[0]
            info_by_field[column]["max"] = unique_values[-1]


    return info_by_field

def get_random_value(unique_values, exclude_min_max=True):
    if exclude_min_max and len(unique_values) > 2:
        return random.choice(unique_values[1:-1])
    return random.choice(unique_values)

def get_random_range(min_val, max_val):
    range_min = random.uniform(min_val, max_val)
    range_max = random.uniform(range_min, max_val)
    return [range_min, range_max]

save_dict = {}

# Iterate through the filenames in the output directory


for filename in tqdm(os.listdir(output_dir), desc="Processing files", unit="file"):
    # Generate corresponding CSV path
    csv_basename = os.path.splitext(filename)[0]
    if "@" not in csv_basename: continue

    csv_filename = f"{csv_basename}.csv"
    save_dict[csv_filename] = {}

    csv_path = os.path.join(csv_dir, csv_filename)
    # print(csv_filename)
    metadata = all_metadata[csv_filename]
    type_by_field = metadata["type_by_field"]
    ambiguous_pairs = metadata["ambiguous_pairs"]
    field_list = metadata["field_list"]
    
    for key, ambi_list in ambiguous_pairs.items():
        key_type = type_by_field[ambi_list[0]]
        type_by_field["[AMBI]"+key] = key_type

    info_by_field = get_info_by_field(csv_path)

    save_unique_values = {}
    for field, info in info_by_field.items():
        unique = info["unique_values"]
        if len(unique) > 2:
            ran = random.randint(1, len(unique) - 2)  # Random index between 1 and len(unique)-2
            save_unique_values[field] = [unique[0], unique[ran], unique[-1]]
        else:
            save_unique_values[field] = unique  # If not enough unique values, save all

    # Generate json path and load json content
    json_path = os.path.join(output_dir, filename)
    
    with open(json_path, 'r') as json_file:
        json_dict = json.load(json_file)
    
    # Process each solution in the json file
    for s_idx, solution in json_dict.items():
        action_list = []
        cur_ambiguous_pairs = {}
        
        # Process each action in the solution's action list
        for action in solution.get("action_list", []):
            a_name, a_op, a_field = action.split(" ")
            
            # Check conditions to skip actions
            if "none" in a_op.lower():
                continue
            if a_name == "encoding" and "none" in a_field.lower():
                continue
            if a_name == "[TERMINAL]":
                continue

            if "[AMBI]" in a_field:
                ambi_key = a_field.split("[AMBI]")[1]
                cur_ambiguous_pairs[ambi_key] = ambiguous_pairs[ambi_key]
            
            new_action = []
            if a_name == "mark":
                new_action = [a_name, a_op]
            elif a_name == "encoding":
                new_action = ["column", a_field]
            elif a_name == "bin":
                if type_by_field[a_field] == "temporal":
                    new_action = [a_name, "year", a_field]
                elif type_by_field[a_field] == "quantitative":
                    new_action = [a_name, "10", a_field]
            elif a_name == "aggregate":
                if a_op == "count":
                    new_action = [a_name, a_op]
                elif a_op in ["sum", "mean"]:
                    new_action = [a_name, a_op, a_field]
            elif a_name == "sort":
                if a_op in ["asc", "desc"]:
                    new_action = [a_name, a_op, a_field]
                else:
                    new_action = [a_name, "asc", a_field]
            elif a_name == "filter":
                field_info = info_by_field[a_field]
                unique_values = field_info["unique_values"]
                min_val = field_info["min"]
                max_val = field_info["max"]

                if a_op in [">=", "<=", "=="]:
                    a_val = get_random_value(unique_values)
                    if type_by_field[a_field] == "temporal":
                        # print(a_val)
                        a_val = pd.to_datetime(a_val)  # Convert string to datetime
                        a_val = a_val.strftime('%Y')  # format value to keep only the year
                        # print(a_val)
                    new_action = [a_name, a_field, a_op, a_val]
                elif a_op == "range":
                    if type_by_field[a_field] == "category":
                        range_list = random.sample(unique_values, min(3, len(unique_values)))
                        new_action = [a_name, a_field, "within", str(range_list)]
                    elif type_by_field[a_field] in ["quantitative"]:
                        range_list = get_random_range(min_val, max_val)
                        
                        # Format float values to keep only 2 decimal places
                        formatted_range_list = [
                            f"{x:.2f}" if isinstance(x, float) else x
                            for x in range_list
                        ]
                        new_action = [a_name, a_field, "within", str(formatted_range_list)]

                    elif type_by_field[a_field] in ["temporal"]:
                        if len(unique_values) < 2:
                            continue
                        range_list = random.sample(range(len(unique_values)), 2)
                        min_val = unique_values[range_list[0]]
                        max_val = unique_values[range_list[1]]
                        min_val = pd.to_datetime(min_val)  # Convert string to datetime
                        max_val = pd.to_datetime(max_val)
                        # print("date: ", end="\t")
                        # print(str([min_val.strftime('%Y'), max_val.strftime('%Y')]))
                        # exit()
                        # format to yyyy-mm-dd
                        # if min_yyyy < max_yyyy, range_list = [min_yyyy, max_yyyy]
                        # elif min_yyyy-mm < max_yyyy-mm, range_list = ["min_yyyy-mm, max_yyyy-mm]
                        # elif min_yyyy-mm-dd < max_yyyy-mm-dd, range_list = ["min_yyyy-mm-dd, max_yyyy-mm-dd]
                        # else range_list has min and max in complete in format yyyy-mm-dd
                        # Format range based on year, month, day
                        if min_val.year < max_val.year:
                            range_list = [min_val.strftime('%Y'), max_val.strftime('%Y')]
                        elif min_val.year == max_val.year and min_val.month < max_val.month:
                            range_list = [min_val.strftime('%Y-%m'), max_val.strftime('%Y-%m')]
                        elif min_val.year == max_val.year and min_val.month == max_val.month and min_val.day < max_val.day:
                            range_list = [min_val.strftime('%Y-%m-%d'), max_val.strftime('%Y-%m-%d')]
                        else:
                            continue

                        
                        # format range list, since the column is datetime, it can be formatted to yyyy-mm-dd, then only keep yyyy
                                              
                        new_action = [a_name, a_field, "within", str(range_list)]
                        print(" ".join([str(item) for item in new_action]))
                        

            # Add valid action to the action list
            if new_action:
                action_list.append(" ".join([str(item) for item in new_action]))
            

            save_cur = {
                "action_list": action_list,
                "ambiguous_pairs": cur_ambiguous_pairs,
                "data_schema": field_list,
                "data_value_example": save_unique_values
            }
            save_dict[csv_filename][s_idx] = save_cur
        
        # print(csv_filename, s_idx, action_list)

    for csv_filename, cur_dict in save_dict.items():
        # Define the path for the JSON file
        json_file_path = os.path.join(save_dir, f"{os.path.basename(csv_filename)}.json")
        cur_dict = convert_int64_to_int(cur_dict)
        # Save the current dictionary to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(cur_dict, json_file, indent=4)