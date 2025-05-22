import os
import json
from tqdm import tqdm  # Import tqdm for progress bar
from util import dict_sorted

T = "temporal"
Q = "quantitative"
C = "category"

nvbench2_list = "./nvbench2_multiprocess/nvbench2.list.json"
metadata_path = "../part1.nvbench_tables/nvbench_metadata.json"
save_dir = "./nvbench2_multiprocess/"

def get_mark(action_list):
    for action in action_list:
        if "mark " in action:
            _, mark = action.split(" ")
            if mark not in [None, "[NONE]"]:
                if mark == "pie": return "arc"
                elif mark == "heatmap": return "rect"
                elif mark == "scatter": return "point"
                else: return mark
    return ["bar", "line", "arc", "point", "rect", "boxplot"]

def solve_ambi_field(ambiguous_pairs, field):
    if "[AMBI]" not in field:
        return field, False
    else:
        field = field.split("[AMBI]")[1]
        return ambiguous_pairs[field], True

def get_field(action_list, ambiguous_pairs, chart_0):
    column_list = []
    for action in action_list:
        if "column " in action:
            _, field = action.split(" ")
            field, ambiguous = solve_ambi_field(ambiguous_pairs, field)
            column_list.append({"field": field, "ambiguous": ambiguous})
    
    filter_list = []
    if "transform" in chart_0:
        for filter in chart_0["transform"]:
            filter_list.append(filter["filter"])
            # print(filter)
            # add filter field to column list
            field = filter["filter"]["field"]
            field, ambiguous = solve_ambi_field(ambiguous_pairs, field)
            field_dict = {"field": field, "ambiguous": ambiguous}
            if field_dict not in column_list:
                column_list.append(field_dict)
        
    return column_list, filter_list

def chart_in_list(chart_list, new_chart):
    for chart in chart_list:
        if new_chart == chart: 
            return True
    return False

def field_in_column_list(column_list, channel_dict):
    if "field" not in channel_dict:
        return None
    # field = c_dict["field"]
    for column_dict in column_list:
        
        # print(column_dict)
        # print(channel_dict)

        if  not column_dict["ambiguous"] and channel_dict["field"] == column_dict["field"]:
            return channel_dict["field"]

        if column_dict["ambiguous"] and channel_dict["field"] in column_dict["field"]:
            return channel_dict["field"]

    return None

def aggre_in_trans_list(trans_list, c_dict, c_field):
    if "aggregate" not in c_dict:
        return None

    for trans in trans_list:
        if "aggregate" not in trans:
            continue
        if trans["aggregate"] == "count":
            if c_field:
                continue
            elif c_dict["aggregate"] == "count":
                return "count"
        else:
            if not c_field:
                continue
            if c_field == trans["field"] or c_field in trans["field"]:
                return c_dict["aggregate"]
            else:
                continue
        return None
    
def bin_in_trans_list(trans_list, c_dict, c_field):
    if "bin" not in c_dict:
        return None
    if not c_field:
        return None
    for trans in trans_list:
        if "bin" not in trans:
            continue
        if c_field == trans["field"] or c_field in trans["field"]:
            return c_dict["bin"]
        
def sort_in_trans_list(trans_list, c_dict, c_field):
    if "sort" not in c_dict:
        return None
    return c_dict["sort"]

def trans_in_column_list(trans_list, c_dict):
    trans_name_list = ["aggregate", "bin", "sort"]
    flag = False
    for trans_name in trans_name_list:
        if trans_name not in c_dict:
            return None
        field = c_dict["field"]
        for c_dict in column_list:
            if not c_dict["ambiguous"] and field == c_dict["field"]:
                return c_dict["field"]
            if c_dict["ambiguous"] and field in c_dict["field"]:
                return c_dict["field"]
    return None

def get_channel_mapping(chart_list, column_list, trans_list):
    # print("column_list:", column_list)
    # print("trans_list:", trans_list)
    new_chart_list = []
    for chart in chart_list:
        # print("old chart: ", chart)
        new_chart = {"mark": chart["mark"], "encoding": {}}
        # print("chart['encoding']", chart["encoding"])
        for c, c_dict in chart["encoding"].items():
            # print("c:", c, "; c_dict:", c_dict)
            new_c_dict ={}

            field = field_in_column_list(column_list, c_dict)
            # print("\tfield:", field)
            if field:
                new_c_dict["field"] = field
            
            aggregate_op = aggre_in_trans_list(trans_list, c_dict, field)
            if aggregate_op:
                new_c_dict["aggregate"] = aggregate_op
            # print("\taggregate_op:", aggregate_op)
            
            bin_op = bin_in_trans_list(trans_list, c_dict, field)
            if bin_op:
                new_c_dict["bin"] = bin_op
            # print("\tbin_op:", bin_op)

            sort_op = sort_in_trans_list(trans_list, c_dict, field)
            if sort_op:
                new_c_dict["sort"] = sort_op
            # print("\tsort_op:", sort_op)
            if new_c_dict != {}:
                new_chart["encoding"][c] = new_c_dict

        # print("new_chart", new_chart)
        # exit()
        if not chart_in_list(new_chart_list, new_chart):
            new_chart_list.append(new_chart)
        # if chart["mark"] == "pie":
        #     print(new_chart)
        #     exit()
    return new_chart_list

def get_additional_channel_mapping(chart_list, column_list, trans_list):
    # print("column_list:", column_list)
    # print("trans_list:", trans_list)
    new_chart_list = []
    for chart in chart_list:
        # print("old chart: ", chart)
        new_chart = {"mark": chart["mark"], "encoding": {}}
        # print("chart['encoding']", chart["encoding"])
        for c, c_dict in chart["encoding"].items():
            # print("c:", c, "; c_dict:", c_dict)
            new_c_dict ={}

            field = None
            if "field" in c_dict:
                field = c_dict["field"]
                new_c_dict["field"] = field
            
            aggregate_op = aggre_in_trans_list(trans_list, c_dict, field)
            if aggregate_op:
                new_c_dict["aggregate"] = aggregate_op
            # print("aggregate_op:", aggregate_op)
            
            bin_op = bin_in_trans_list(trans_list, c_dict, field)
            if bin_op:
                new_c_dict["bin"] = bin_op
            # print("bin_op:", bin_op)

            sort_op = sort_in_trans_list(trans_list, c_dict, field)
            if sort_op:
                new_c_dict["sort"] = sort_op
            # print("sort_op:", sort_op)
            if new_c_dict != {}:
                new_chart["encoding"][c] = new_c_dict

        # print("new_chart", new_chart)
        if not chart_in_list(new_chart_list, new_chart):
            new_chart_list.append(new_chart)
        # if chart["mark"] == "pie":
        #     print(new_chart)
        #     exit()
    return new_chart_list

def get_transformation(column_list, action_list, type_by_field):
    trans_list = []
    for action in action_list:
        # if not action start with "aggregate" or "bin" or "sort"
        if not (action.startswith("aggregate") or action.startswith("bin") or action.startswith("sort")):
            continue
        # print(action)
        if "aggregate count" in action:
            a_name, a_op = action.split(" ")
            trans_list.append({
                    "aggregate": a_op
                })
        else:
            a_name, a_op, a_field = action.split(" ")
            field, ambiguous = solve_ambi_field(ambiguous_pairs, a_field)

            if a_name == "aggregate":
                trans_list.append({
                    "field": field,
                    "aggregate": a_op
                })
            elif a_name == "bin":
                bin_Q = {"maxbins": 10}
                bin_T = "year"
                core_field = field[0] if isinstance(field, list) else field
                field_type = type_by_field[core_field]
                trans_list.append({
                    "field": field,
                    "bin": bin_T if field_type == T else bin_Q
                })
            elif a_name == "sort":
                trans_list.append({
                    "field": field,
                    "sort": "ascending" if a_op == "asc" else "descending"
                })

    return trans_list

# def chart_list_identical(chart_list_1, chart_list_2):
#     print("chart_list_1:", chart_list_1)
#     print("chart_list_2:", chart_list_2)
#     if len(chart_list_1) != len(chart_list_2):
#         return False

#     sorted_chart_list_1 = [dict_sorted(chart) for chart in chart_list_1]
#     sorted_chart_list_2 = [dict_sorted(chart) for chart in chart_list_2]
    
#     # Sort both chart lists
#     sorted_chart_list_1 = sorted(chart_list_1, key=lambda x: str(x))
#     sorted_chart_list_2 = sorted(chart_list_2, key=lambda x: str(x))
    
#     # Compare each chart in the sorted lists
#     for chart_1, chart_2 in zip(sorted_chart_list_1, sorted_chart_list_2):
#         if chart_1 != chart_2:
#             return False
            
#     return True


if __name__ == "__main__":

    with open(nvbench2_list, 'r') as file:
        dataset = json.load(file)

    with open(metadata_path, 'r') as metadata_file:
        all_metadata = json.load(metadata_file)

    new_dataset = []

    for idx in tqdm(range(len(dataset)), desc="Processing datasets"):
        input = dataset[idx]["input"]
        chart_list = dataset[idx]["output"]

        csv_file = dataset[idx]["csv_file"]
        action_list = dataset[idx]["action_list"]
        ambiguous_pairs = all_metadata[csv_file]["ambiguous_pairs"]
        type_by_field = all_metadata[csv_file]["type_by_field"]

        print("\n\n### data idx: ", idx)
        # print("input: ", chart_list)

        new_data = dataset[idx]
        new_data["steps"] = {}
        
        # step 1: data selection
        print("# Solving answers for step 1...")
        column_list, filter_list = get_field(action_list, ambiguous_pairs, chart_list[0])
        step_1_answer = {"column_list": column_list, "filter_list": filter_list}
        new_data["steps"]["step_1"] = {
                                        "reasoning": None,
                                        "answer": step_1_answer
                                    }
        print(step_1_answer)

        # step 2: data transformation
        print("# Solving answers for step 2...")
        trans_list = get_transformation(column_list, action_list, type_by_field)
        step_2_answer = trans_list
        new_data["steps"]["step_2"] = {
                                        "reasoning": None,
                                        "answer": step_2_answer
                                }
        print(step_2_answer)

        # step 3: chart selection
        print("# Solving answers for step 3...")
        mark_list = get_mark(action_list)
        step_3_answer = mark_list
        new_data["steps"]["step_3"] = {
                                        "reasoning": None,
                                        "answer": step_3_answer
                                    }
        print(step_3_answer)

        # step 4: channel mapping
        print("# Solving answers for step 4...")
        cur_chart_list = get_channel_mapping(chart_list, column_list, trans_list)
        step_4_answer = cur_chart_list
        new_data["steps"]["step_4"] = {
                                "reasoning": None,
                                "answer": step_4_answer
                            }
        print(step_4_answer)

        # step 5: Additional channel mapping
        print("# Solving answers for step 5...")
        cur_chart_list = get_additional_channel_mapping(chart_list, column_list, trans_list)
        step_5_answer = cur_chart_list
        new_data["steps"]["step_5"] = {
                            "reasoning": None,
                            "answer": step_5_answer
                        }
        print(step_5_answer)

        # step 6: Additional transformation
        print("# Solving answers for step 6...")
        step_6_answer = chart_list
        new_data["steps"]["step_6"] = {
                            "reasoning": None,
                            "answer": step_6_answer
                        }
        print(step_6_answer)

        new_dataset.append(new_data)

        # print("output: ", new_data["output"])

        # if len(new_dataset) > 10:
        #     exit()

    new_save_path = os.path.join(save_dir, "nvbench2.step.json")
    # save new_dataset
    with open(new_save_path, 'w') as f:
        json.dump(new_dataset, f, indent=4)
    