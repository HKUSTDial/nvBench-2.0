from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from mark import Q, C, T
from mark import mark_enc_type_dict, mark_bin_dict, mark_aggregate_dict
from table import TableInfo
from asp import solve_chart, process_ambiguous_pairs, convert_format
import draco
from date_column import load_and_parse_csv
import pandas as pd


TERMINAL = "[TERMINAL]"

@dataclass
class State:
    """Abstract base class for game state"""
    def get_legal_actions(self) -> List[int]:
        raise NotImplementedError
        
    def take_action(self, action: int) -> 'State':
        raise NotImplementedError
        
    def is_terminal(self) -> bool:
        raise NotImplementedError
        
    def get_score(self) -> float:
        raise NotImplementedError
        
    def get_state_action_prior(self, action: int) -> float:
        """Compute prior probability P(s,a) for current state and action"""
        raise NotImplementedError
    
def normalize_to_prob(numbers):
    total = sum(numbers)
    return [n/total for n in numbers]

class Action:
    def __init__(self, name, op=None, field=None, field_type=None, value=None, channel=None):
        self.name = name
        self.op = op
        self.field = field
        self.field_type = field_type
        self.value = value
        self.channel = channel

    def __str__(self):
        return str(self.name) + " " + str(self.op) + " " + str(self.field)

def get_mark_actions():
    new_actions = []
    for mark in list(mark_enc_type_dict.keys()):
        cur = Action("mark", mark)
        new_actions.append(cur)
    new_actions_prior = [ 1 for _ in range(len(new_actions))]
    
    # print(new_actions)
    return new_actions, normalize_to_prob(new_actions_prior)

def get_encoding_actions(mark, encoding, fields_by_type):
    field_type_list = mark_enc_type_dict[mark][encoding]
    new_actions = []
    new_actions_prior = []
    for field_type in field_type_list:
        for field in fields_by_type[field_type]:
            cur = Action("encoding", encoding, field, field_type)
            new_actions.append(cur)
            if "[AMBI]" in field: tmp = 2
            else: tmp = 1
            new_actions_prior.append(tmp)
    cur = Action("encoding", encoding, "[NONE]", "[NONE]")
    new_actions.append(cur)
    new_actions_prior.append(1)
    
    # new_actions_prior = [ 1 for _ in range(len(new_actions))]
    return new_actions, normalize_to_prob(new_actions_prior)


def get_bin_actions(mark, channel, field, field_type):
    bin = False
    # ops_T = ["year", "month", "weekday", "[NONE]"]
    ops_T = ["true", "[NONE]"]
    ops_Q = ["true",  "[NONE]"]
    new_actions = []

    target_type_list = mark_bin_dict[mark][channel]

    if target_type_list == []:
        cur = Action("bin", "[NONE]", "[NONE]")
        new_actions.append(cur)
    else:
        if field_type in target_type_list:
            bin = True
            if field_type == T: ops = ops_T
            elif field_type == Q: ops = ops_Q
        else:
            bin = False
            field = "[NONE]"
            ops = ["[NONE]"]
    
        for op in ops:
            cur = Action("bin", op, field)
            new_actions.append(cur)
    
    new_actions_prior = [ 1 for _ in range(len(new_actions))]
    return new_actions, normalize_to_prob(new_actions_prior)
    
def get_aggregate_actions(mark, state):
    aggregate = False
    channels = mark_aggregate_dict[mark]
    field = None
    for channel in channels:
        for action in state:
            if action.name == "encoding" and action.op == channel:
                if action.field not in ["[NONE]", None]:
                    field = action.field
                    break
        if field is not None: break

    if field in ["[NONE]", None]:
        ops = ["count", "[NONE]"]
        # new_actions_prior = [5, 5]
    else:
        ops = ["sum", "mean", "[NONE]"]
        # new_actions_prior = [2, 2, 1, 1, 6]

    new_actions = []
    for op in ops:
        cur = Action("aggregate", op, field)
        new_actions.append(cur)

    new_actions_prior = [ 1 for _ in range(len(new_actions))]
    return new_actions, normalize_to_prob(new_actions_prior)

def get_sort_actions(mark, field_X, field_type_X, field_Y, field_type_Y):
    X_C = False
    ops = ["asc", "desc", "[ANY]", "[NONE]"]
    new_actions = []

    if mark in ["bar", "pie", "[NONE]"] and field_type_X == C and field_type_Y == Q:
        # print("sort here!")
        X_C = True
        for op in ops:
            cur = Action("sort", op, field_Y, channel="y")
            new_actions.append(cur)
    else:
        cur = Action("sort", "[NONE]", "[NONE]")
        new_actions.append(cur)
    
    new_actions_prior = [ 1 for _ in range(len(new_actions))]
    return new_actions, normalize_to_prob(new_actions_prior)

def get_filter_actions(fields_by_type, encoded_fields, terminal_prob = 0.5):
    new_actions = []
    new_actions_prior = []

    tmp_actions = []
    # for op in ["range", "=="]:
    for op in ["range"]:
        for field_type in [Q, T, C]:
            if fields_by_type[field_type] == []:
                continue

            for field in fields_by_type[field_type]:
                if "[AMBI]" in field: continue
                if field not in encoded_fields: continue
                cur = Action("filter", op, field, field_type)
                tmp_actions.append(cur)

    tmp_actions_prior =[ ((1 - terminal_prob) * 0.5) / len(tmp_actions) for _ in range(len(tmp_actions))]
    new_actions += tmp_actions
    new_actions_prior += tmp_actions_prior

    for op in [">=", "<="]:
        for field_type in [Q, T]:
            for field in fields_by_type[field_type]:
                if "[AMBI]" in field: continue
                if field not in encoded_fields: continue
                cur = Action("filter", op, field, field_type)
                tmp_actions.append(cur)
    tmp_actions_prior =[ ((1 - terminal_prob) * 0.5) / len(tmp_actions) for _ in range(len(tmp_actions))]
    new_actions += tmp_actions
    new_actions_prior += tmp_actions_prior

    cur = Action(TERMINAL)
    new_actions.append(cur)
    new_actions_prior.append(terminal_prob)
    # print("fields_by_type:", fields_by_type)
    # print("encoded_fields:", encoded_fields)
    # print("filter:", [str(action) for action in new_actions])
    # print("prior:", new_actions_prior)
    # exit()
    # print(new_actions_prior)

    return new_actions, new_actions_prior


class VQLState(State):
    def __init__(self, table_info: TableInfo = None, input_state: list = [], action_name_idx: int = 0):
        # print("new idx:", action_name_idx)

        self.table_info = table_info
        self.csv_path = table_info.csv_path
        self.field_by_type = table_info.field_by_type_ambi
        # self.data_schema = table_info.data_schema
        self.ambiguous_pairs = table_info.ambi_column_pairs

        # print("field_by_type: ", self.field_by_type)
        # exit()

        # self.action_channels = ['x', 'y', 'color', 'size', 'column']
        self.action_channels = ['x', 'y', 'color', 'size']
        self.action_bins = [['bin', 'x'], ['bin', 'y']]
        # self.action_aggs = [['aggregate', 'y'], ['aggregate', 'color'], ['aggregate', 'size']]
        
        self.action_names = ['mark'] + self.action_channels + self.action_bins + ['aggregate', 'sort'] + ['filter' for _ in range(4)]

        self.state = input_state
        self.action_name_idx = action_name_idx

        self.current_actions = None
        self.current_state_action_prior = None

        if input_state == []: self.mark = None
        else: self.mark = input_state[0].op


        self.set_avaliable_encoding_field_by_type()
        self.set_avaliable_filter_field_by_type()

    def __str__(self):
        output = ""
        for action in self.state:
            output += str(action) + "\n"
        
        return output

    def set_avaliable_encoding_field_by_type(self):
        encoded_fields = []
        for action in self.state:
            if action.name == "encoding":
                if action.field not in ["[NONE]", None]:
                    encoded_fields.append(action.field)
                    if "[AMBI]" in action.field:
                        ambi_name = action.field.split("[AMBI]")[1]
                        field_list = self.ambiguous_pairs[ambi_name]
                        for c_field in field_list:
                            encoded_fields.append(c_field)

        self.encoded_fields = encoded_fields

        self.avaliable_encoding_field_by_type = {}
        for f_type in [Q, C, T]:
            cur_list = []
            for field in self.field_by_type[f_type]:
                if field not in encoded_fields:
                    cur_list.append(field)
            self.avaliable_encoding_field_by_type[f_type] = cur_list

    def set_avaliable_filter_field_by_type(self):
        filtered_fields = []
        for action in self.state:
            if action.name == "filter":
                if action.field not in ["[NONE]", None]:
                    filtered_fields.append(action.field)

        self.avaliable_filter_field_by_type = {}
        for f_type in [Q, C, T]:
            cur_list = []
            for field in self.field_by_type[f_type]:
                if field not in filtered_fields:
                    cur_list.append(field)
            self.avaliable_filter_field_by_type[f_type] = cur_list

    def get_field_type_by_channel(self, channel):
        field = None
        field_type = None
        for action in self.state:
            if action.name == "encoding" and action.op == channel:
                field = action.field
                field_type = action.field_type
                break
        return field, field_type
    

    def get_legal_actions(self) -> List[int]:
        """
        Returns:
            List[int]: List of legal action integers
        """
        if self.current_actions:
            return self.current_actions

        # print("self.action_name_idx", self.action_name_idx)
        # print("self.action_names[self.action_name_idx]", self.action_names[self.action_name_idx])
         
        if self.action_names[self.action_name_idx] == 'mark':
            self.current_actions, self.current_state_action_prior = get_mark_actions()

        if self.action_names[self.action_name_idx] in self.action_channels:
            channel = self.action_names[self.action_name_idx]
            self.current_actions, self.current_state_action_prior = get_encoding_actions(self.mark, channel, self.avaliable_encoding_field_by_type)
        
        if self.action_names[self.action_name_idx] in self.action_bins:
            channel = self.action_names[self.action_name_idx][1]
            field, field_type = self.get_field_type_by_channel(channel)
            self.current_actions, self.current_state_action_prior = get_bin_actions(self.mark, channel, field, field_type)
        
        if self.action_names[self.action_name_idx] == 'aggregate':
            # channel = self.action_names[self.action_name_idx][1]
            # field, field_type = self.get_field_type_by_channel(channel)
            self.current_actions, self.current_state_action_prior = get_aggregate_actions(self.mark, self.state)
        
        if self.action_names[self.action_name_idx] == 'sort':
            channel = self.action_names[self.action_name_idx][1]
            if self.mark == "pie":
                field_X, field_type_X = self.get_field_type_by_channel("color")
                field_Y, field_type_Y = self.get_field_type_by_channel("y")
            else:
                field_X, field_type_X = self.get_field_type_by_channel("x")
                field_Y, field_type_Y = self.get_field_type_by_channel("y")
            self.current_actions, self.current_state_action_prior = get_sort_actions(self.mark, field_X, field_type_X, field_Y, field_type_Y)

        if self.action_names[self.action_name_idx] == 'filter':
            self.current_actions, self.current_state_action_prior = get_filter_actions(self.avaliable_filter_field_by_type, self.encoded_fields)

        # for action in self.current_actions:
        #     print(action)
        return self.current_actions
        
    def get_legal_actions_prior(self):
        return self.current_state_action_prior

    def take_action(self, action) -> 'State':
        """
        Apply the given action to current state and return new resulting state.
        IMPORTANT: Should not modify current state, but return a new state object.
        
        Args:
            action: dict
            
        Returns:
            State: New state object after applying action
        """
        # new_self_state = self.state + action # 改成字典
        if self.action_name_idx < len(self.action_names):
            new_action_name_idx = self.action_name_idx + 1
        else:
            return None

        # print("new_action_name_idx", new_action_name_idx)
        new_self_state = self.state + [action]
        # print("new action: ", action)
        # print("new state: ", new_self_state)
        new_state = VQLState(self.table_info, new_self_state, new_action_name_idx)
        # exit()

        return new_state
        
    def is_terminal(self) -> bool:
        """
        Returns:
            bool: True if state is terminal, False otherwise
        """
        if self.state == []:
            return False

        last_action = self.state[-1]
        if last_action.name == TERMINAL or len(self.state) == len(self.action_names):
            return True
        else:
            return False
    
    def more_ignore_column_list(self):
        filtered_field_list = []
        for action in self.state:
            if action.name == "filter":
                field = action.field
                field = field.replace("[AMBI]", "")
                filtered_field_list.append(field)

        more_ignore_column_list = []
        for field in self.field_by_type[C]:
            if "[AMBI]" in field:
                continue
            if field not in filtered_field_list and self.table_info.unique_value_num[field] > 20:
                more_ignore_column_list.append(field)
        return more_ignore_column_list

    def get_k_value(self) -> float:
        # action list to chart config
        chart_config = transform_state_to_chart_config(self.state)

        # # from 
        # df = load_and_parse_csv(self.csv_path)
        # data_schema = draco.schema_from_dataframe(df)
        data_schema = self.table_info.get_data_schema(self.more_ignore_column_list())

        # chart config + data schema config
        # print("\nself.data_schema:\n", self.data_schema)
        combined_config = {**chart_config, **data_schema}

        # dict to asp rules
        asp_rules = draco.dict_to_facts(combined_config)
        asp_rules = convert_format(asp_rules)

        # solve asp
        # print("\nnew asp!")
        # print("asp_rules:", asp_rules)
        # print("ambiguous_pairs:", self.ambiguous_pairs)
        asp_rules = process_ambiguous_pairs(asp_rules, ambiguous_pairs=self.ambiguous_pairs)
        result = solve_chart(asp_rules)

        # compute k = |V|
        k = len(result)

        return k, result
        
    # def get_score(self) -> float:
    #     """
    #     Calculate and return a score for current state.
    #     Higher scores should indicate better states.
        
    #     * ASP here
        
    #     Returns:
    #         float: Score value for this state
    #     """

    #     # action list to chart config
    #     chart_config = transform_state_to_chart_config(self.state)

    #     # # from 
    #     # df = load_and_parse_csv(self.csv_path)
    #     # data_schema = draco.schema_from_dataframe(df)

    #     # chart config + data schema config
    #     combined_config = {**chart_config, **self.data_schema}

    #     # dict to asp rules
    #     asp_rules = draco.dict_to_facts(combined_config)
    #     asp_rules = convert_format(asp_rules)

    #     # solve asp
    #     # print("\nnew asp!")
    #     # print("asp_rules:", asp_rules)
    #     # print("ambiguous_pairs:", self.ambiguous_pairs)
    #     asp_rules = process_ambiguous_pairs(asp_rules, ambiguous_pairs=self.ambiguous_pairs)
    #     result = solve_chart(asp_rules)

    #     # compute k = |V|
    #     k = len(result)

    #     # score
    #     if k in [2, 3, 4, 5]:
    #         score = 0
    #     if k > 5:
    #         score = - min(k, 10)
    #     if k == 1:
    #         score = -5
    #     if k == 0:
    #         score = - 10

    #     return score
        
    def get_state_action_prior(self, action: int) -> float:
        action_idx = None
        for a_idx in range(len(self.current_actions)):
            if action == self.current_actions[a_idx]:
                action_idx = a_idx
        return self.current_state_action_prior[action_idx]


chart_type_to_mark = {
    "bar": "bar", 
    "line": "line",
    "pie": "pie",
    "scatter": "point",
    "boxplot": "boxplot",
    "heatmap": "rect",
    "[NONE]": None,
    # "[NONE]": None
}

def transform_state_to_chart_config(state):
    chart_config = {
            "view": [
                {
                    "mark": [
                        {
                            "encoding": []
                        }
                    ],
                    "scale": []
                }
            ]
        }
    
    by_field = {}
    for action in state:
        # none
        if action.op in ["[NONE]", None, "[TERMINAL]"]:
            continue
        if action.name == "encoding" and action.field in ["[NONE]", None]:
            continue
        
        # mark
        if action.name == "mark":
            chart_config["view"][0]["mark"][0]["type"] = chart_type_to_mark[action.op]

        # encoding
        if action.name == "encoding":
            by_field[action.field] = {}
        
        # bin
        if action.name == "bin":
            if action.op in ["true", True]: by_field[action.field]["binning"] = 10
            else: by_field[action.field]["binning"] = action.op
        
        # aggregate
        if action.name == "aggregate":
            if action.op == "count": 
                new_encoding = {"aggregate": "count"}
                chart_config["view"][0]["mark"][0]["encoding"].append(new_encoding)
            else:
                # print(action.op)
                by_field[action.field]["aggregate"] = action.op

        # sort
        # pass!!!!

        # filter
        # pass!!!!

    for field, f_dict in by_field.items():

        new_encoding = {"field": field}
        if "binning" in f_dict:
            new_encoding["binning"] = f_dict["binning"]
        if "aggregate" in f_dict:
            new_encoding["aggregate"] = f_dict["aggregate"]

        chart_config["view"][0]["mark"][0]["encoding"].append(new_encoding)

    return chart_config


            






